## Purpose

Provides a layered, accessible visual system for the SOS Drive landing hero while preserving the existing content and keeping all frontend behavior in Python and Reflex.

## ADDED Requirements

### Requirement: Layered landing hero presentation

The landing hero SHALL preserve its existing headline, supporting copy, assistance panel, trust chips, CTA, and “Como funciona” content while presenting them above intentional visual depth layers.

#### Scenario: Hero renders with layered depth
- **WHEN** the landing page loads
- **THEN** the hero displays the existing content above orange and trust-blue blurred glow layers without changing the content wording or order

#### Scenario: Hero remains usable without optional illustrations
- **WHEN** no illustration asset exists in the local assets folder
- **THEN** the hero renders its complete content and layout without a broken image, exception, or visible placeholder

### Requirement: Glow and floating illustration effects

The landing hero SHALL use subtle, non-synchronous glow and illustration motion that remains decorative and does not block interaction.

#### Scenario: Glow layers animate independently
- **WHEN** motion is enabled
- **THEN** the orange and blue background glows pulse with different delays and remain behind the readable content

#### Scenario: Local illustrations float independently
- **WHEN** one or more supported local transparent images are available
- **THEN** each displayed illustration has a drop shadow and an independent duration/delay/rotation so the elements do not move in lockstep

### Requirement: Reusable glass panel

The visual system SHALL provide a glassmorphism treatment for the assistance panel and future highlight cards.

#### Scenario: Assistance panel uses glass treatment
- **WHEN** the “Visão da assistência” panel renders
- **THEN** it has a translucent surface, backdrop blur where supported, a thin translucent border, a large radius, and a diffuse shadow with an opaque/translucent fallback where blur is unavailable

### Requirement: Hero hierarchy and interactive emphasis

The hero SHALL use a strong typographic hierarchy, translucent trust chips, and a visually prominent emergency CTA without changing their semantic meaning.

#### Scenario: Headline hierarchy is clear
- **WHEN** the hero renders
- **THEN** its headline uses large bold typography with tight tracking, one meaningful keyword in emergency orange, and supporting text uses neutral color with comfortable line height

#### Scenario: Chips and CTA respond to hover
- **WHEN** a pointer hovers a trust chip or the primary CTA
- **THEN** the element elevates subtly and the CTA intensifies its orange-family shadow without excessive motion

### Requirement: Reduced-motion and contrast accessibility

The landing hero SHALL remain legible and usable under WCAG 2.2 AA expectations and SHALL disable all decorative motion when reduced motion is requested.

#### Scenario: Reduced motion is requested
- **WHEN** the browser exposes `prefers-reduced-motion: reduce`
- **THEN** glow pulses, illustration floating, hover transitions, and transforms are disabled or reduced to an instantaneous change while content remains visible

#### Scenario: Text remains readable over effects
- **WHEN** glow and glass layers are present
- **THEN** normal text maintains at least 4.5:1 contrast against its effective background and interactive focus remains visible

### Requirement: Responsive hero layout

The hero SHALL adapt its decorative layers and content layout to desktop and mobile widths without horizontal scrolling or obscuring the CTA.

#### Scenario: Desktop hero renders
- **WHEN** the viewport is desktop width
- **THEN** the hero presents layered illustrations around the content and keeps the assistance panel visually balanced beside the text

#### Scenario: Mobile hero renders
- **WHEN** the viewport is mobile width
- **THEN** text, CTA, chips, and assistance panel reflow into a readable vertical composition, with decorative assets reduced or hidden as needed
