// Hares v2 rule — per memory_2565 (2026-10-06), refined: Hare is a body,
// not a land bridge. Fail-mode override counts FUNCTIONAL lands (Nykthos
// half, Field colorless-risk) and requires a LAND-finder/rock, not just Hare.
const landVal = c => {
  if (!c.l) return 0;
  const t = c.t || [];
  if (c.n === "Fabled Passage") return 0.5;
  if (t.includes("half")) return 0.5;
  return 1;
};
const isLandBridge = c => !c.l && ["Ambitious Farmhand","Knight of the White Orchid","Loyal Warhound","Arcane Signet","The Mind Stone","Mind Stone","Pearl Medallion"].includes(c.n.split(" // ")[0]);
const isBridge = c => isLandBridge(c) || (!c.l && (c.n === "Hare Apparent" || c.n === "Esper Sentinel"));
const isStranded = c => !c.l && ((c.t || []).includes("stranded"));
const earlyPlay = c => !c.l && (c.c <= 2 || isBridge(c));
const ruleKeepV2 = hand => {
  const lands = hand.filter(c => c.l).length;
  const f = hand.reduce((s, c) => s + landVal(c), 0);
  if (lands <= 1 || lands >= 6) return { keep: false, why: lands + " lands — base rule mulls 0/1/6/7" };
  const stranded = hand.filter(isStranded).length;
  const landBridge = hand.some(isLandBridge);
  const early = hand.some(earlyPlay);
  const colorlessRisk = hand.some(c => c.l && ((c.t || []).includes("colorless")));
  if (f < 2) return { keep: false, why: "only " + f + " functional lands (Nykthos/Lotus Field count half)" };
  if (stranded >= 2 && !landBridge)
    return { keep: false, why: "fail-mode: " + stranded + " stranded 4-5s with no land-finder/rock (Hare is a body, not a bridge)" };
  if (!early)
    return { keep: false, why: "no play before turn 3 — dead vs token/ramp curves" };
  if (colorlessRisk && f <= 2)
    return { keep: true, why: "keep, thin: a colorless land can delay white mana — find white by T3", warn: true };
  return { keep: lands >= 2 && lands <= 5, why: lands + " lands with bridge/early action" };
};

// Standard token decks need a board start plus a follow-up, not just lands.
const standardStarters = ["Optimistic Scavenger","Warden of the Inner Sky",
  "Resolute Reinforcements","Hare Apparent"];
const ruleKeepStandard = hand => {
  const lands = hand.filter(c => c.l).length;
  if (lands <= 1 || lands >= 6)
    return { keep: false, why: lands + " lands — mulligan 0/1/6/7" };
  const hasStarter = hand.some(c => !c.l && standardStarters.includes(c.n.split(" // ")[0]));
  const hasArmorTarget = hand.some(c => !c.l && ["Optimistic Scavenger",
    "Warden of the Inner Sky","Resolute Reinforcements","Hare Apparent"]
    .includes(c.n.split(" // ")[0]));
  const earlyActions = hand.filter(c => !c.l && c.c <= 3 &&
    (c.n.split(" // ")[0] !== "Ethereal Armor" || hasArmorTarget)).length;
  if (!hasStarter)
    return { keep: false, why: "no turn-1/2 board starter (Scavenger, Warden, Reinforcements, or Hare)" };
  if (earlyActions < 2)
    return { keep: false, why: "board starter but fewer than 2 spells with mana value 3 or less" };
  return { keep: true, why: lands === 5
    ? "5 lands kept only with a board starter and 2 spells with mana value 3 or less"
    : lands + " lands with a board starter and 2 spells with mana value 3 or less" };
};

const scoreOpeningHand = (hand, selectedDeck) => {
  if (!selectedDeck) return null;
  const playable = hand.filter(c => !c.l);
  const mv = c => {
    const cost = (c.m || "").split("//")[0];
    if (!cost) return c.c || 0;
    return [...cost.matchAll(/\{([^}]+)\}/g)].reduce((sum, match) => {
      const numeric = match[1].match(/\d+/g);
      if (numeric) return sum + Math.max(...numeric.map(Number));
      return sum + (/^[XYZ]$/i.test(match[1]) ? 0 : 1);
    }, 0);
  };
  const t1 = playable.filter(c => mv(c) <= 1).length;
  const t2 = playable.filter(c => mv(c) === 2).length;
  const t3 = playable.filter(c => mv(c) === 3).length;
  const landCount = hand.filter(c => c.l).length;
  const hasT1 = landCount >= 1 && t1 > 0;
  const hasT2 = landCount >= 2 && t2 > 0;
  const hasT3 = landCount >= 3 && t3 > 0;
  const expectedLands = 7 * (selectedDeck.lands || 0) / (selectedDeck.size || 60);
  const landFit = Math.max(0, 100 - Math.abs(landCount - expectedLands) * 28);
  const kind = c => c.k || "";
  const role = c => (c.r || "").toLowerCase();
  const interactionCards = playable.filter(c =>
    ["removal", "protect", "interaction"].includes(role(c)) ||
    (kind(c) === "instant" && mv(c) <= 3)).length;
  const threatCards = playable.filter(c =>
    ["threat", "payoff", "hare"].includes(role(c)) ||
    ((kind(c) === "creature" || kind(c) === "planeswalker") && mv(c) <= 4)).length;
  const synergyCards = playable.filter(c =>
    ["payoff", "hare", "token", "engine"].includes(role(c))).length;
  const fastThreats = playable.filter(c =>
    (kind(c) === "creature" || kind(c) === "planeswalker" ||
     ["threat", "payoff", "hare"].includes(role(c))) && mv(c) <= 3).length;

  return {
    velocity: (hasT1 ? 35 : 0) + (hasT2 ? 25 : 0) + (hasT3 ? 15 : 0) +
      (hasT1 && hasT2 && hasT3 ? 25 : 0),
    consistency: Math.round(landFit * 0.75 + Math.min(100, (t1 + t2 + t3) * 25) * 0.25),
    interaction: Math.min(100, interactionCards * 35),
    efficiency: Math.min(100, t1 * 28 + t2 * 18 + t3 * 8),
    lethality: Math.min(100, fastThreats * 20 + synergyCards * 12 + Math.max(0, threatCards - fastThreats) * 8)
  };
};

const ruleKeep = handOrN => {
  if (typeof handOrN === "number") return handOrN >= 2 && handOrN <= 5;
  if (deck && deck.rule === "hares-v2") return ruleKeepV2(handOrN).keep;
  if (deck && (deck.rule === "standard-pg-v1" || deck.rule === "standard-ph-v1"))
    return ruleKeepStandard(handOrN).keep;
  const lands = handOrN.filter(c => c.l).length;
  return lands >= 2 && lands <= 5;
};
const ruleWhy = hand => {
  if (deck && deck.rule === "hares-v2") return ruleKeepV2(hand);
  if (deck && (deck.rule === "standard-pg-v1" || deck.rule === "standard-ph-v1"))
    return ruleKeepStandard(hand);
  const lands = hand.filter(c => c.l).length;
  const k = lands >= 2 && lands <= 5;
  return { keep: k, why: lands + " lands — base 2-5 rule" };
};
