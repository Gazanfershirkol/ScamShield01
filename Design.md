# UI/UX Design System & Interface Specification — ScamShield AI

## 1. Design Philosophy & Principles

ScamShield AI prioritizes **Clarity, Trust, Cyber-Vigilance, and Accessibility**.
- **Credible Cybersecurity Aesthetic:** A professional, dark-mode-first terminal/dashboard feel (deep slate, neon-toned functional accents, high-contrast typography) that conveys serious analytical capability without distracting game-like animations.
- **Never Rely on Color Alone:** Every security verdict is identified by three distinct visual attributes: a high-contrast color badge, a recognized universal icon, and explicit textual severity labels (`Likely Safe`, `Needs Review`, `Likely Scam`).
- **Explainability Front and Center:** Evidence and detected patterns are treated as primary information, not hidden in nested submenus. Users should immediately comprehend *why* a verdict was reached.
- **Responsible Restraint:** No sensationalist flashing warnings. Probabilistic disclaimers are visible on every screen.

---

## 2. Color Tokens & Palette

The design utilizes a tailored CSS custom property tokens system based on deep slate backgrounds and high-contrast semantic indicators compliant with **WCAG 2.1 AA** contrast ratios (minimum 4.5:1 for normal text, 3:1 for large UI components).

```css
:root {
  /* Surface & Background */
  --bg-primary: #0B0F19;         /* Ultra-deep slate background */
  --bg-surface: #111827;         /* Primary container surface */
  --bg-surface-elevated: #1F2937;/* Elevated cards, dropdowns, inputs */
  --border-subtle: #374151;      /* Default subtle border */
  --border-active: #4B5563;      /* Focused element border */

  /* Primary Brand & Accents */
  --primary-accent: #0EA5E9;     /* Cyan/Sky blue - active highlights & buttons */
  --primary-hover: #38BDF8;      /* Lighter cyan for hover states */
  --primary-glow: rgba(14, 165, 233, 0.15);

  /* Semantic Verdict Colors */
  /* 1. Likely Safe */
  --safe-bg: #064E3B;            /* Deep forest emerald */
  --safe-border: #059669;        /* Medium emerald */
  --safe-text: #34D399;          /* High-contrast mint green */
  --safe-icon: #10B981;

  /* 2. Needs Review */
  --review-bg: #451A03;          /* Deep amber/brown */
  --review-border: #D97706;      /* Vibrant amber */
  --review-text: #FBBF24;        /* Bright golden amber */
  --review-icon: #F59E0B;

  /* 3. Likely Scam */
  --scam-bg: #4C0519;            /* Deep crimson maroon */
  --scam-border: #E11D48;        /* Vivid rose/crimson */
  --scam-text: #FDA4AF;          /* Soft crimson text */
  --scam-icon: #F43F5E;

  /* Typography Colors */
  --text-primary: #F9FAFB;       /* Pure white / light grey */
  --text-secondary: #9CA3AF;     /* Muted secondary grey */
  --text-tertiary: #6B7280;      /* Darker placeholder grey */
  --text-link: #38BDF8;

  /* Status Tokens */
  --danger: #EF4444;
  --success: #10B981;
  --warning: #F59E0B;
}
```

---

## 3. Typography Hierarchy

- **Primary Typeface:** `Inter`, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Monospace Typeface (for URLs, tokens, metrics):** `JetBrains Mono`, `Fira Code`, Consolas, monospace.

| Element | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Title (`h1`)** | `1.875rem` (30px) | `700` (Bold) | `1.2` | App Header Title & Brand |
| **Section Title (`h2`)** | `1.25rem` (20px) | `600` (SemiBold) | `1.3` | Section Headers (Analysis, Verdict, Evidence) |
| **Card Header (`h3`)** | `1.0rem` (16px) | `600` (SemiBold) | `1.4` | Sub-card headings (Text Signals, URL Signals) |
| **Body Text (`p`)** | `0.9375rem` (15px) | `400` (Regular) | `1.5` | Descriptions, explanatory paragraphs |
| **Verdict Badge** | `1.125rem` (18px) | `700` (Bold) | `1.2` | High-impact verdict label (`LIKELY SCAM`) |
| **Risk Score Display**| `2.5rem` (40px) | `800` (ExtraBold) | `1.0` | Large numerical score (`88 / 100`) |
| **Technical Tokens** | `0.8125rem` (13px) | `500` (Medium) | `1.4` | URL paths, domain tags, identified keywords |
| **Disclaimers / Small**| `0.75rem` (12px) | `400` (Regular) | `1.4` | Responsible use legal note & model limits |

---

## 4. Spacing, Layout & Responsive Grid

The layout follows an 8px grid system (`0.25rem`, `0.5rem`, `0.75rem`, `1rem`, `1.5rem`, `2rem`, `3rem`).

### Responsive Breakpoints:
- **Mobile (`< 640px`):** Single-column stacked layout. Inputs full width. Buttons span 100% width. Score and verdict stack vertically.
- **Tablet (`640px – 1024px`):** 2-column input/result arrangement where appropriate; compact padding.
- **Desktop (`> 1024px`):** Maximum container width `1100px` centered. Side-by-side or cleanly divided two-panel interface (Left: Submission & Quick Samples; Right: Verdict & Real-time Evidence Breakdown).

---

## 5. Component Hierarchy & Wireframe Structure

```text
+-----------------------------------------------------------------------------------+
|  [Logo] ScamShield AI   |   KLE BCA Coding Club · AI · 03   |  [Evaluation Modal]  |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---------------------------------------+  +----------------------------------+  |
|  | INPUT WORKSPACE                       |  | VERDICT & EVIDENCE DISPLAY       |  |
|  |                                       |  |                                  |  |
|  | [1] Message Text:                     |  |  +----------------------------+  |  |
|  | +-----------------------------------+ |  |  | VERDICT: LIKELY SCAM [!]   |  |  |
|  | | "Your SBI account is locked..."   | |  |  | RISK SCORE: 92 / 100        |  |  |
|  | +-----------------------------------+ |  |  +----------------------------+  |  |
|  |                                       |  |                                  |  |
|  | [2] URL to Inspect:                   |  |  [+] Text Signals Breakdown      |  |
|  | +-----------------------------------+ |  |      - Urgency phrases detected  |  |
|  | | http://sbi-kyc-verify.xyz/login   | |  |      - Account threat keywords   |  |
|  | +-----------------------------------+ |  |                                  |  |
|  |                                       |  |  [+] URL Signals Breakdown       |  |
|  | [ Quick Presets: Bank | Job | Safe ]  |  |      - Non-standard TLD (.xyz)   |  |
|  |                                       |  |      - Brand impersonation (sbi) |  |
|  | [ ANALYZE NOW (Ctrl+Enter) ] [ Clear ]|  |                                  |  |
|  |                                       |  |  [!] Recommended Protection Plan |  |
|  +---------------------------------------+  +----------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  [Disclaimer: Probabilistic AI assessment. Does not replace personal vigilance.] |
+-----------------------------------------------------------------------------------+
```

---

## 6. Component Specifications & Behavior

### 6.1 Input Form
- **Message Input Area:** Expanding `<textarea>` with character counter (`0 / 10,000`). Clear placeholder indicating expected format.
- **URL Input Field:** `<input type="url">` with automatic protocol prefixing helper (`http://` / `https://`) and character counter (`0 / 2,048`).
- **Sample Preset Chips:** Clickable pill buttons allowing evaluators to immediately populate:
  - Preset 1: *Bank Impersonation Phishing (SMS + Link)*
  - Preset 2: *Work-from-Home Recruitment Scam (Text only)*
  - Preset 3: *Deceptive Shortlink / Free Gift (URL only)*
  - Preset 4: *Legitimate Delivery Notification (Safe message + Benign domain)*
- **Action Buttons:**
  - `Analyze Button`: Primary cyan filled button with keyboard shortcut tooltip `[Ctrl + Enter]`.
  - `Reset Button`: Secondary ghost button to wipe inputs and reset UI state.

### 6.2 Verdict Presentation
The verdict banner is visually prominent and includes:
1. **Icon:**
   - Safe: Shield with Checkmark (SVG).
   - Review: Triangle with Exclamation Point (SVG).
   - Scam: Octagon with Warning Shield / Skull (SVG).
2. **Text Label:** `LIKELY SAFE` | `NEEDS REVIEW` | `LIKELY SCAM`.
3. **Score Gauge / Progress Bar:** Clean animated horizontal meter displaying the exact numerical score `0–100` with color-stops.
4. **Confidence Note:** Explicit badge indicating whether confidence is High (e.g. `95% Confidence`) or Moderate (e.g. `Conflicting Indicators — Manual Verification Advised`).

### 6.3 Evidence Cards
Structured into two distinct collapsible/expandable sections:
- **Textual Evidence:** Tags displaying detected scam keywords (red pill tags) and safe keywords (green pill tags), alongside linguistic pattern flags.
- **URL Evidence:** Monospace domain breakdown highlighting suspicious structural elements (unusual TLD, excessive subdomains, presence of IP address).

---

## 7. UI States Specification

1. **Empty State:**
   - Input fields are blank.
   - Result card displays an empty container with a subtle dashed border and prompt: *"Awaiting input. Enter a suspect message, link, or choose a preset scenario to evaluate risk."*
2. **Loading State:**
   - Analyze button enters disabled state with subtle CSS spinner.
   - Result panel displays a sleek skeleton shimmer screen matching the verdict card layout.
   - Accessible announcement: `aria-busy="true"` on the result container.
3. **Success State:**
   - Skeleton transitions cleanly into the completed verdict card with full evidence breakdown and recommended actions.
4. **Validation Error State:**
   - If user triggers analysis with both inputs blank, or exceeds max characters:
   - A non-intrusive alert banner appears above the input form: *"Please provide at least a message text or a valid URL to analyze."*
   - Focus is shifted back to the text area.
5. **Server Error / Network Error State:**
   - If API fails or server is unreachable:
   - Alert banner displays: *"Analysis service unavailable. Check that the local server is running on port 8000."*

---

## 8. Accessibility & Responsible UX Standards

- **Keyboard Traversal:** All interactive controls (`textarea`, `input`, `button`, preset chips) have clearly visible high-contrast `:focus-visible` outlines (`2px solid var(--primary-accent)` with 2px offset).
- **Screen Reader Support:** Semantic HTML tags (`<main>`, `<header>`, `<footer>`, `<section>`, `<article>`, `<button>`). Result changes are wrapped in an `aria-live="polite"` region.
- **Contrast Ratios:** Text-to-background contrast exceeds 7:1 for headers and 4.8:1 for body copy.
- **Mandatory Uncertainty Disclaimer:** Displayed persistently at the bottom of the dashboard in a muted, non-intrusive footer:
  > *"ScamShield AI is an automated risk-assessment tool built for academic demonstration. Risk scores reflect pattern recognition and heuristics; they do not guarantee safety or prove criminal intent. Never submit private passwords or financial PINs into third-party evaluators."*
