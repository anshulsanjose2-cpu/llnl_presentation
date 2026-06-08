// ============================================================
//  Presentation config — edit these values, no HTML changes needed.
//  After editing, hard-reload the page (Cmd-Shift-R) to pick it up.
// ============================================================
window.PRESENTATION_CONFIG = {
  // Content lock — hides the deck behind a countdown until the specified UTC time.
  // 9:00 AM Pacific (PDT = UTC-7) on Wed Jun 10, 2026 == 16:00 UTC
  contentLock: {
    enabled: true,
    showAtUTC: "2026-06-10T16:00:00Z"
  },

  draftBanner: {
    // Master switch. Set to false to hide the banner immediately.
    enabled: true,

    // Banner text.
    text: "WORK IN PROGRESS",

    // Auto-hide at this instant, written in UTC (the "Z" means UTC).
    //   6:00 AM Pacific (PDT) on Wed Jun 10, 2026  ==  13:00 UTC
    // Set to null to keep the banner up until you flip `enabled` to false.
    hideAtUTC: "2026-06-10T13:00:00Z"
  }
};
