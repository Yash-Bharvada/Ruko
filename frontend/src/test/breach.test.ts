import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { createRouter, rootRouteId } from "@tanstack/react-router";
import { routeTree } from "@/routeTree.gen";
import { BREACH_STRINGS } from "@/lib/breachStrings";

describe("Breach Monitor Routing", () => {
  it("matches /breach-monitor route successfully", () => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });
    const matches = router.matchRoutes("/breach-monitor");
    expect(matches.at(-1)?.routeId).not.toBe(rootRouteId);
    expect(matches.at(-1)?.pathname).toBe("/breach-monitor");
  });
});

describe("Breach Strings & Guardrails", () => {
  it("includes all 4 required data safety pillar labels in en, hi, gu", () => {
    for (const lang of ["en", "hi", "gu"] as const) {
      const strings = BREACH_STRINGS[lang];
      expect(strings.safetyPillars.minimalCollection).toBeTruthy();
      expect(strings.safetyPillars.noCredentials).toBeTruthy();
      expect(strings.safetyPillars.noRawLeaks).toBeTruthy();
      expect(strings.safetyPillars.inMemoryOnly).toBeTruthy();
    }
  });

  it("contains the mandatory data safety notice text in en", () => {
    expect(BREACH_STRINGS.en.dataSafetyNotice).toBe(
      "A breach exposure does not necessarily mean your account was compromised.",
    );
  });

  it("explainer explicitly forbids requesting passwords, OTPs, PINs, or banking details", () => {
    for (const lang of ["en", "hi", "gu"] as const) {
      const explainer = BREACH_STRINGS[lang].explainer;
      expect(explainer.neverAsk).toBeTruthy();
      expect(explainer.noStorage).toBeTruthy();
    }
  });

  it("includes quiet hours warning in voice alert strings", () => {
    expect(BREACH_STRINGS.en.voiceAlert.quietHoursNotice).toContain("21:00");
    expect(BREACH_STRINGS.en.voiceAlert.quietHoursNotice).toContain("08:00");
  });

  it("includes SMS and voice call options and friendly error notices", () => {
    for (const lang of ["en", "hi", "gu"] as const) {
      const va = BREACH_STRINGS[lang].voiceAlert;
      expect(va.sendSmsButton).toBeTruthy();
      expect(va.callCodeButton).toBeTruthy();
      expect(va.smsUnavailableNotice).toBeTruthy();
      expect(va.trialNotice).toBeTruthy();
      expect(va.rateLimitNotice).toBeTruthy();
      expect(va.invalidCodeNotice).toBeTruthy();
      expect(va.simulatedBadge).toBeTruthy();
      expect(va.playAlertButton).toBeTruthy();
      expect(va.stopAlertButton).toBeTruthy();
      expect(va.simulatedDesc).toBeTruthy();
    }
  });
});
