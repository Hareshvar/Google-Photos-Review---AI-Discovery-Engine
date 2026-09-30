---
name: Retrieval Lens
colors:
  surface: '#faf9fd'
  surface-dim: '#dbd9dd'
  surface-bright: '#faf9fd'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f7'
  surface-container: '#efedf1'
  surface-container-high: '#e9e7eb'
  surface-container-highest: '#e3e2e6'
  on-surface: '#1a1b1e'
  on-surface-variant: '#414754'
  inverse-surface: '#2f3033'
  inverse-on-surface: '#f1f0f4'
  outline: '#727785'
  outline-variant: '#c1c6d6'
  surface-tint: '#005bc0'
  primary: '#005bbf'
  on-primary: '#ffffff'
  primary-container: '#1a73e8'
  on-primary-container: '#ffffff'
  inverse-primary: '#adc7ff'
  secondary: '#5b5f64'
  on-secondary: '#ffffff'
  secondary-container: '#dde0e6'
  on-secondary-container: '#5f6368'
  tertiary: '#006d2c'
  on-tertiary: '#ffffff'
  tertiary-container: '#008939'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc7ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#dfe3e8'
  secondary-fixed-dim: '#c3c7cc'
  on-secondary-fixed: '#181c20'
  on-secondary-fixed-variant: '#43474c'
  tertiary-fixed: '#89fa9b'
  tertiary-fixed-dim: '#6ddd81'
  on-tertiary-fixed: '#002108'
  on-tertiary-fixed-variant: '#005320'
  background: '#faf9fd'
  on-background: '#1a1b1e'
  surface-variant: '#e3e2e6'
  google-blue-tint: '#e8f0fe'
  google-red: '#ea4335'
  google-red-tint: '#fce8e6'
  google-yellow: '#fbbc04'
  google-yellow-tint: '#fef7e0'
  google-green-tint: '#e6f4ea'
  surface-bg: '#f8f9fa'
  surface-card: '#ffffff'
  border-subtle: '#dadce0'
typography:
  headline-lg:
    fontFamily: Roboto Flex
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Roboto Flex
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Roboto Flex
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.1px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

# Stitch Design Brief: Retrieval Lens (Google Photos Discovery Engine)

## 0. What this product is
"Retrieval Lens" is a research tool, not a consumer app. It shows findings from an AI analysis of public posts (app reviews, Reddit, forums) about people struggling to find old photos in Google Photos when their memory of the photo is incomplete. The audience is a product researcher and reviewers — people reading findings, checking evidence quotes, and asking a chatbot questions. It should feel credible, calm, and evidence-first — not like a marketing dashboard.

## 1. Global design system
### 1.1 Visual identity: Google Photos, replicated faithfully
Base the whole visual language on Google Photos and Material 3: clean, light, generous white space, rounded shapes, friendly and calm. No dark mode. No gradients, no glassmorphism, no stock photography.

Colours:
- Blue: Base `#1A73E8` / `#4285F4`, Tint `#E8F0FE` (Info, confidence, primary actions)
- Red: Base `#EA4335`, Tint `#FCE8E6` (Failures, search broke)
- Yellow: Base `#FBBC04`, Tint `#FEF7E0` (Caution, low confidence)
- Green: Base `#34A853`, Tint `#E6F4EA` (Success, validated, confirmed)
- Neutrals: background `#F8F9FA`, card surface `#FFFFFF`, primary text `#202124`, secondary text `#5F6368`, dividers `#DADCE0`.
- Typography: Google Sans / Roboto / Inter. Min text 14px.
- Shape: pill buttons, 16px corner radius on cards, subtle borders/shadows.
