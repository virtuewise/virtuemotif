import test from "node:test";
import assert from "node:assert/strict";
import { createHorizonWorld } from "../film/src/fur3d/HorizonCinematicWorld.ts";

const cue = {
  time: 72,
  beatPulse: 0.8,
  energy: 0.7,
  transitionIntensity: 0.5,
  hasAudioCues: true,
};

test("Horizon cinematic world mounts named environment layers and disposes GPU resources", () => {
  const world = createHorizonWorld();
  const names = world.group.children.map((child) => child.name);

  assert.ok(names.includes("cinematic-sky"));
  assert.ok(names.includes("far-mountains"));
  assert.ok(names.includes("middle-mountains"));
  assert.ok(names.includes("near-ridge"));
  assert.ok(names.includes("red-earth"));
  assert.ok(names.includes("river-of-light"));
  assert.ok(names.includes("journey-portal"));
  assert.ok(names.includes("ancestral-stars"));
  assert.ok(names.includes("golden-journey-particles"));

  world.update(72, cue, "The night remembers our shadows", "Verse");
  assert.equal(world.group.getObjectByName("ancestral-stars").visible, true);

  world.dispose();
  assert.equal(world.group.children.length, 0);
});

test("Horizon environment responds deterministically to the same lyric and audio frame", () => {
  const first = createHorizonWorld();
  const second = createHorizonWorld();

  first.update(18, cue, "Hope brings a new morning light", "Chorus");
  second.update(18, cue, "Hope brings a new morning light", "Chorus");

  const firstPortal = first.group.getObjectByName("journey-portal");
  const secondPortal = second.group.getObjectByName("journey-portal");
  const firstSun = first.group.getObjectByName("horizon-sun");
  const secondSun = second.group.getObjectByName("horizon-sun");

  assert.equal(firstPortal.visible, true);
  assert.equal(firstPortal.visible, secondPortal.visible);
  assert.deepEqual(firstPortal.scale.toArray(), secondPortal.scale.toArray());
  assert.deepEqual(firstSun.position.toArray(), secondSun.position.toArray());

  first.dispose();
  second.dispose();
});


test("Horizon world themes recognize Shona, Ndebele, and Zulu lyric vocabulary", () => {
  const world = createHorizonWorld();

  world.update(12, cue, "Ebusuku sikhumbula amanzi", "Verse");
  assert.equal(world.group.getObjectByName("ancestral-stars").visible, true);
  assert.equal(world.group.getObjectByName("river-of-light").visible, true);

  world.update(24, cue, "Mvura inounza tariro nechiedza", "Verse");
  assert.equal(world.group.getObjectByName("river-of-light").visible, true);
  assert.equal(world.group.getObjectByName("journey-portal").visible, true);

  world.update(36, cue, "Ekuseni ithemba nokukhanya", "Verse");
  assert.equal(world.group.getObjectByName("journey-portal").visible, true);

  world.dispose();
});

test("Imported world dressing is not gated by English-only travel keywords", () => {
  const world = createHorizonWorld();
  world.update(8, cue, "Siyahamba sonke", "Verse");
  assert.equal(world.group.getObjectByName("licensed-world-assets").visible, true);
  world.dispose();
});
