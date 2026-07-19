## ADDED Requirements

### Requirement: Bridge publisht Wärmetauscher-Status
Die Vallox-Bridge SHALL den Wärmetauscher-Betriebszustand (`A_CYC_CELL_STATE`) als Integer-Wert über MQTT publizieren. Gültige Werte: 0 (Wärmerückgewinnung), 1 (Kälterückgewinnung), 2 (Bypass), 3 (Abtauung).

#### Scenario: cell_state wird bei jedem Poll-Zyklus publiziert
- **WHEN** die Bridge eine Metrik-Abfrage vom Vallox durchführt
- **THEN** wird `cell_state` zusammen mit allen anderen Metriken auf `ventilation/vallox/cell_state` publiziert

#### Scenario: Bypass ist aktiv
- **WHEN** der Vallox im Bypass-Modus läuft (`A_CYC_CELL_STATE = 2`)
- **THEN** erscheint der Wert `2` auf dem MQTT-Topic

### Requirement: Δ-Panel im Ventilations-Dashboard zeigt symmetrische Farbzonen
Das Panel `Δ Zuluft − Innenluft (Wärmeeintrag)` SHALL den Temperatur-Unterschied mit symmetrischen Schwellen in beide Richtungen und farbigen Hintergrundzonen (nicht nur Linienfarbwechsel) darstellen.

#### Scenario: Zuluft kühlt stark
- **WHEN** Δ < −3 °C
- **THEN** Hintergrund dunkelblau (starke Kühlung sichtbar)

#### Scenario: Zuluft kühlt leicht
- **WHEN** −3 °C ≤ Δ < −1 °C
- **THEN** Hintergrund hellblau

#### Scenario: Δ neutral
- **WHEN** −1 °C ≤ Δ ≤ +1 °C
- **THEN** Hintergrund grün

#### Scenario: Zuluft heizt leicht
- **WHEN** +1 °C < Δ ≤ +3 °C
- **THEN** Hintergrund orange

#### Scenario: Zuluft heizt stark
- **WHEN** Δ > +3 °C
- **THEN** Hintergrund rot

### Requirement: Überblick-Dashboard zeigt kompakten Lüftungs-Effekt
Das Überblick-Dashboard SHALL ein zusätzliches Stat-Panel `Lüftungs-Effekt` enthalten, das in zwei nebeneinanderliegenden Feldern den aktuellen thermischen Effekt der Lüftung anzeigt.

#### Scenario: Delta-Feld zeigt Zuluft-Effekt
- **WHEN** das Panel geladen wird
- **THEN** zeigt Feld 1 den Wert `Zuluft − Innenluft` in °C mit symmetrischen Farbschwellen (identisch zum Ventilations-Dashboard)

#### Scenario: Status-Feld zeigt Wärmetauscher-Modus als Text
- **WHEN** `cell_state = 0`
- **THEN** zeigt Feld 2 den Text „Wärmerückgewinnung" mit grünem Hintergrund

#### Scenario: Bypass-Modus im Status-Feld
- **WHEN** `cell_state = 2`
- **THEN** zeigt Feld 2 den Text „Bypass" mit blauem Hintergrund

#### Scenario: Abtauung im Status-Feld
- **WHEN** `cell_state = 3`
- **THEN** zeigt Feld 2 den Text „Abtauung" mit rotem Hintergrund
