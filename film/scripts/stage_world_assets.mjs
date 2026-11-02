#!/usr/bin/env node
/**
 * Stage immutable, manifest-pinned GLBs into the local asset tree.
 *
 * Downloads never auto-approve art or licensing. Files enter staged-review;
 * a human must inspect each model and then explicitly approve its manifest row.
 */
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("../../", import.meta.url)));
const manifestPath = resolve(root, "film/assets/world/asset-manifest.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const sources = {
  "baobab-tree": "https://cdn.3dassets.dev/assets/37714/v1/model.glb",
  "large-acacia-tree": "https://cdn.3dassets.dev/assets/37713/v1/model.glb",
  "small-acacia-tree": "https://cdn.3dassets.dev/assets/37712/v1/model.glb",
  "grand-touring-coupe": "https://cdn.3dassets.dev/assets/18681/v1/model.glb",
};

const only = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));
const selected = only.length ? only : Object.keys(sources);
const failures = [];
for (const id of selected) {
  const asset = manifest.assets.find((entry) => entry.id === id);
  const url = sources[id];
  if (!asset || !url) {
    failures.push(`Unknown or unsupported asset: ${id}`);
    continue;
  }
  try {
    const response = await fetch(url, { redirect: "error" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length < 20 || bytes.toString("ascii", 0, 4) !== "glTF") {
      throw new Error("Response is not a binary GLB");
    }
    const declaredLength = bytes.readUInt32LE(8);
    if (declaredLength !== bytes.length) {
      throw new Error(`GLB length header mismatch (${declaredLength} != ${bytes.length})`);
    }
    const digest = createHash("sha256").update(bytes).digest("hex");
    const destination = resolve(root, asset.file);
    if (!destination.startsWith(root + "/")) throw new Error("Asset path escapes repository root");
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, bytes);
    asset.sha256 = digest;
    asset.status = "staged-review";
    asset.stagedFrom = url;
    console.log(`STAGED ${id}: ${bytes.length} bytes sha256=${digest}`);
  } catch (error) {
    failures.push(`${id}: ${error instanceof Error ? error.message : String(error)}`);
  }
}
await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
for (const failure of failures) console.error(`FAIL ${failure}`);
if (failures.length) process.exitCode = 1;
else console.log("Staging complete. Assets remain staged-review until human inspection and explicit approval.");
