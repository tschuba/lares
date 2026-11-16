# Changelog

## 1.0.0 (2026-11-16)


### Features

* add battery level timeseries panel to energy dashboard ([b4b8f20](https://github.com/tschuba/lares/commit/b4b8f20bde9dd430f6bdc98f5437b8802195bff9))
* add display names for temperature and humidity metrics in weather dashboard ([8dfb135](https://github.com/tschuba/lares/commit/8dfb135cb86e254161d7d32fb02e414209205f91))
* add display names for temperature metrics in heating dashboard and enhance field configurations ([ed65dce](https://github.com/tschuba/lares/commit/ed65dce98e839810aebad8c10833df2b3d69fc69))
* add Grafana provisioning configuration and initial system, energy, and weather dashboards ([8630b5c](https://github.com/tschuba/lares/commit/8630b5c63f8cba5be50a1cbde0d6d9b164e342f0))
* add heating indoor metrics and update air quality visualization in ventilation dashboard ([509da49](https://github.com/tschuba/lares/commit/509da492da432b7c943d076c59733a662e21ddfb))
* add rainfall metrics to weather dashboard with custom display options ([ec973c4](https://github.com/tschuba/lares/commit/ec973c42b8609d99284349c1b118b25f2a917e0c))
* add ventilation dashboard configuration for Vallox with various metrics and visualizations ([efdbdd2](https://github.com/tschuba/lares/commit/efdbdd21680ed9f306519a4fd63459bdb0f86566))
* add ventilation heating alert rule to monitor temperature differences ([900e95e](https://github.com/tschuba/lares/commit/900e95ebc2bfd57848de7115bf397f41f772f498))
* enhance energy dashboard queries for heating and hot water metrics ([f483923](https://github.com/tschuba/lares/commit/f483923d5d086d473e8a6c267544fcf053d0dc65))
* enhance Telegraf configuration for system metrics and update Docker setup ([b374cad](https://github.com/tschuba/lares/commit/b374cad660d0f41a674e12d66868a91431d39811))
* fritz2mqtt bridge for FRITZ!Smart Energy 250 ([#11](https://github.com/tschuba/lares/issues/11)) ([58d9c7b](https://github.com/tschuba/lares/commit/58d9c7b8b78a3e81dad17910f3d78e83816c852b))
* **grafana-alerts:** improve Pushover notification readability ([#22](https://github.com/tschuba/lares/issues/22)) ([401e4ac](https://github.com/tschuba/lares/commit/401e4ac6e31cda52829e7a801e32c13b7f9f2a1c))
* **grafana:** add combined temperature panel to heating dashboard ([#26](https://github.com/tschuba/lares/issues/26)) ([1d9b5d4](https://github.com/tschuba/lares/commit/1d9b5d4be8249413c0039a485e982ea4b9581f2b))
* **grafana:** Config-Image für Dashboards und Provisioning (ADR-020) ([#36](https://github.com/tschuba/lares/issues/36)) ([37cb12b](https://github.com/tschuba/lares/commit/37cb12b109398a1d332b132df7848881b0137f93))
* **grafana:** Heizung – Zähler als Balken, Zählerstände, Erzeuger-Status (Verdichter/Heizstab), Dev-Instanz ([#28](https://github.com/tschuba/lares/issues/28)) ([0328d29](https://github.com/tschuba/lares/commit/0328d29c75727e19e29c874c9f6996b9bef84bc6))
* **grafana:** Heizung-Dashboard überarbeitet (Zählerstände-Layout, Panels) ([#31](https://github.com/tschuba/lares/issues/31)) ([8d98be7](https://github.com/tschuba/lares/commit/8d98be72a295cdf4c4335ccf320bee0ecd8fd00b))
* **grafana:** improve Aktueller Status panel readability ([#16](https://github.com/tschuba/lares/issues/16)) ([f34e9c1](https://github.com/tschuba/lares/commit/f34e9c1efdde7c316ad65d8b72db110295aa5e05))
* **grafana:** Lüftungs-Dashboard-Redesign + Außenluft-Innenluft-Skala ([#19](https://github.com/tschuba/lares/issues/19)) ([d7d05d2](https://github.com/tschuba/lares/commit/d7d05d257418b661ab6956a7510eb63564da67ed))
* **grafana:** Überblick-Dashboard + Cross-Dashboard-Navigation ([#13](https://github.com/tschuba/lares/issues/13)) ([df98e58](https://github.com/tschuba/lares/commit/df98e580759c2f067c9f27d9866237655b09caab))
* implement ntfy alerting integration with Grafana for heat pump and inverter errors ([62f6778](https://github.com/tschuba/lares/commit/62f677868cfa315b56ced1181457b0992b9453ef))
* **lüftung:** Lüftungs-Effekt-Anzeige + cell_state Bridge ([832074e](https://github.com/tschuba/lares/commit/832074ec539c761026eabd733a750f76a2c1b458))
* **monitoring-alerts:** Bridge-Erweiterungen + 13 Grafana-Alert-Regeln ([#20](https://github.com/tschuba/lares/issues/20)) ([3423251](https://github.com/tschuba/lares/commit/3423251744098640e8e535fd4cf103bf79ad37aa))
* **monitoring:** fault monitoring with Pushover push and Alerta inbox (ADR-019) ([#35](https://github.com/tschuba/lares/issues/35)) ([906ad4c](https://github.com/tschuba/lares/commit/906ad4c6c023c130870af82a0e4b2eb95aa39378))
* pin all Docker image tags and add release-gated bridge builds ([#25](https://github.com/tschuba/lares/issues/25)) ([7b8448a](https://github.com/tschuba/lares/commit/7b8448af1c592af58cb16f0032c5fd16fa669f68))
* update ventilation heating rule to include outdoor air condition and extend duration ([2bba273](https://github.com/tschuba/lares/commit/2bba27345da729f11cbcce5b78134f8e2876af75))


### Bug Fixes

* **grafana-alerts:** migrate threshold → classic_conditions in all alert rules ([#21](https://github.com/tschuba/lares/issues/21)) ([5ea537b](https://github.com/tschuba/lares/commit/5ea537b6ab34fb89107bd793ff49efe66821db30))
* **grafana:** repeat BMS alarm push only once per day ([#37](https://github.com/tschuba/lares/issues/37)) ([664f60d](https://github.com/tschuba/lares/commit/664f60ddec8b8786134e7de892ebde9e060f578b))
* update matcher options and refine query for indoor heating metrics in ventilation dashboard ([6ec24f0](https://github.com/tschuba/lares/commit/6ec24f0cb1818f68fce2a30b75d208f4f0495a96))
* update matcher options for heating indoor and delta metrics in ventilation dashboard ([f3d62d6](https://github.com/tschuba/lares/commit/f3d62d6c22f338accbe982924066fb5aab41c43d))
* update time range in system dashboard to show daily data ([a7e5ea8](https://github.com/tschuba/lares/commit/a7e5ea8734a14d7bea4b7b387aca259bc4696ce8))
