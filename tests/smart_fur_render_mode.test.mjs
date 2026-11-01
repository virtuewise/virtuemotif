import test from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULT_SMART_FUR_RENDER_ACTION,
  resolveSmartFurRenderAction,
} from "../film/src/fur3d/smartFurRenderMode.ts";

test("production renders always use the stable default action", () => {
  assert.deepEqual(resolveSmartFurRenderAction(false), DEFAULT_SMART_FUR_RENDER_ACTION);
  assert.deepEqual(
    resolveSmartFurRenderAction(false, { fogDensity: 0.55, beatSensitivity: 2.2 }),
    DEFAULT_SMART_FUR_RENDER_ACTION,
  );
});

test("adaptive preview accepts only bounded learned action values", () => {
  assert.deepEqual(
    resolveSmartFurRenderAction(true, { fogDensity: 0.55, beatSensitivity: 2.2 }),
    { fogDensity: 0.55, beatSensitivity: 2.2 },
  );
  assert.deepEqual(resolveSmartFurRenderAction(true, null), DEFAULT_SMART_FUR_RENDER_ACTION);
  assert.deepEqual(
    resolveSmartFurRenderAction(true, { fogDensity: 1.2, beatSensitivity: 2 }),
    DEFAULT_SMART_FUR_RENDER_ACTION,
  );
  assert.deepEqual(
    resolveSmartFurRenderAction(true, { fogDensity: 0.2, beatSensitivity: Number.NaN }),
    DEFAULT_SMART_FUR_RENDER_ACTION,
  );
  assert.deepEqual(
    resolveSmartFurRenderAction(true, { fogDensity: 0.2, beatSensitivity: 0 }),
    DEFAULT_SMART_FUR_RENDER_ACTION,
  );
});
