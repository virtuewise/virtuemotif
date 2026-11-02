#!/usr/bin/env node
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve, relative, isAbsolute, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("../../", import.meta.url)));
const manifestPath = resolve(root, "film/assets/world/asset-manifest.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const production = process.argv.includes("--production");
const failures = [];
const warnings = [];
const approvedLicenses = new Set(["CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0"]);

for (const asset of manifest.assets ?? []) {
  if (!asset.id || !asset.file || !asset.license || !asset.source) {
    failures.push(`[${asset.id ?? "unknown"}] missing required provenance fields`);
    continue;
  }
  if (isAbsolute(asset.file) || asset.file.split(/[\\/]/).includes("..")) {
    failures.push(`[${asset.id}] unsafe asset path: ${asset.file}`);
    continue;
  }
  const absolute = resolve(root, asset.file);
  if (!absolute.startsWith(root + sep)) {
    failures.push(`[${asset.id}] path escapes repository root`);
    continue;
  }
  if (!asset.licenseEvidence || !/^https:\/\//i.test(asset.licenseEvidence)) failures.push(`[${asset.id}] missing valid HTTPS licence evidence`);
  if (!approvedLicenses.has(asset.license)) failures.push(`[${asset.id}] unapproved or unknown licence identifier: ${asset.license}`);
  if (!asset.sha256 || !/^[a-f0-9]{64}$/i.test(asset.sha256)) {
    const message = `[${asset.id}] SHA-256 is not pinned`;
    (production ? failures : warnings).push(message);
  }
  try {
    const bytes = await readFile(absolute);
    if (bytes.length < 12 || bytes.toString("ascii", 0, 4) !== "glTF") {
      failures.push(`[${asset.id}] file is not a binary GLB: ${asset.file}`);
      continue;
    }
    const actual = createHash("sha256").update(bytes).digest("hex");
    if (asset.sha256 && actual !== asset.sha256.toLowerCase()) {
      failures.push(`[${asset.id}] checksum mismatch (expected ${asset.sha256}, got ${actual})`);
    }
  } catch {
    const message = `[${asset.id}] local asset missing: ${asset.file}`;
    (production ? failures : warnings).push(message);
  }
  if (production && asset.status !== "approved-local") {
    failures.push(`[${asset.id}] status must be approved-local (currently ${asset.status})`);
  }
  if (production && /^https?:/i.test(asset.file)) {
    failures.push(`[${asset.id}] production asset paths must be repository-local`);
  }
}

for (const warning of warnings) console.warn(`WARN ${warning}`);
for (const failure of failures) console.error(`FAIL ${failure}`);
if (failures.length) process.exitCode = 1;
else console.log(`Asset provenance validation passed for ${manifest.assets.length} manifest entries.`);
