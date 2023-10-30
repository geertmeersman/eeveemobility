<img src="https://github.com/geertmeersman/eeveemobility/raw/main/images/brand/logo.png"
     alt="Eevee Mobililty"
     align="right"
     style="width: 200px;margin-right: 10px;" />

# Eevee Mobililty for Home Assistant

A Home Assistant integration to monitor Eevee Mobililty

## Features

- All Eevee Mobililty sensors

---

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->

[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20a%20Duvel-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)
[![discord](https://img.shields.io/discord/1104706338111627385?style=for-the-badge&logo=discord)](https://discord.gg/wZHsA4aGvS)

[![MIT License](https://img.shields.io/github/license/geertmeersman/eeveemobility?style=flat-square)](https://github.com/geertmeersman/eeveemobility/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=eeveemobility&category=integration)

[![GitHub issues](https://img.shields.io/github/issues/geertmeersman/eeveemobility)](https://github.com/geertmeersman/eeveemobility/issues)
[![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/geertmeersman/eeveemobility.svg)](http://isitmaintained.com/project/geertmeersman/eeveemobility)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/geertmeersman/eeveemobility.svg)](http://isitmaintained.com/project/geertmeersman/eeveemobility)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/geertmeersman/eeveemobility/pulls)

[![Hacs and Hassfest validation](https://github.com/geertmeersman/eeveemobility/actions/workflows/validate.yml/badge.svg)](https://github.com/geertmeersman/eeveemobility/actions/workflows/validate.yml)
[![Python](https://img.shields.io/badge/Python-FFD43B?logo=python)](https://github.com/geertmeersman/eeveemobility/search?l=python)

[![manifest version](https://img.shields.io/github/manifest-json/v/geertmeersman/eeveemobility/master?filename=custom_components%2Feeveemobility%2Fmanifest.json)](https://github.com/geertmeersman/eeveemobility)
[![github release](https://img.shields.io/github/v/release/geertmeersman/eeveemobility?logo=github)](https://github.com/geertmeersman/eeveemobility/releases)
[![github release date](https://img.shields.io/github/release-date/geertmeersman/eeveemobility)](https://github.com/geertmeersman/eeveemobility/releases)
[![github last-commit](https://img.shields.io/github/last-commit/geertmeersman/eeveemobility)](https://github.com/geertmeersman/eeveemobility/commits)
[![github contributors](https://img.shields.io/github/contributors/geertmeersman/eeveemobility)](https://github.com/geertmeersman/eeveemobility/graphs/contributors)
[![github commit activity](https://img.shields.io/github/commit-activity/y/geertmeersman/eeveemobility?logo=github)](https://github.com/geertmeersman/eeveemobility/commits/main)

<!-- [END BADGES] -->

## Table of contents

- [Eevee Mobililty for Home Assistant](#eevee-mobililty-for-home-assistant)
  - [Features](#features)
  - [Table of contents](#table-of-contents)
  - [Installation](#installation)
    - [Using HACS (recommended)](#using-hacs-recommended)
    - [Manual](#manual)
  - [Contributions are welcome!](#contributions-are-welcome)
  - [Troubleshooting](#troubleshooting)
    - [Frequently asked questions](#frequently-asked-questions)
    - [Enable debug logging](#enable-debug-logging)
    - [Disable debug logging and download logs](#disable-debug-logging-and-download-logs)
  - [Lovelace examples](#lovelace-examples)
  - [Screenshots](#screenshots)

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

**Click on this button:**

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=eeveemobility&category=integration)

**or follow these steps:**

1. Simply search for `Eevee Mobililty` in HACS and install it easily.
2. Restart Home Assistant
3. Add the 'Eevee Mobililty' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Eevee Mobililty configuration details

### Manual

1. Copy the `custom_components/eeveemobility` directory of this repository as `config/custom_components/eeveemobility` in your Home Assistant instalation.
2. Restart Home Assistant
3. Add the 'eeveemobility' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Eevee Mobililty configuration details

This integration will set up the following platforms.

| Platform        | Description                                 |
| --------------- | ------------------------------------------- |
| `eeveemobility` | Home Assistant component for Eevee Mobility |

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Troubleshooting

### Frequently asked questions

### Enable debug logging

To enable debug logging, go to Settings -> Devices & Services and then click the triple dots for the Eevee Mobililty integration and click Enable Debug Logging.

![enable-debug-logging](https://raw.githubusercontent.com/geertmeersman/eeveemobility/main/images/screenshots/enable-debug-logging.gif)

### Disable debug logging and download logs

Once you enable debug logging, you ideally need to make the error happen. Run your automation, change up your device or whatever was giving you an error and then come back and disable Debug Logging. Disabling debug logging is the same as enabling, but now you will see Disable Debug Logging. After you disable debug logging, it will automatically prompt you to download your log file. Please provide this logfile.

![disable-debug-logging](https://raw.githubusercontent.com/geertmeersman/eeveemobility/main/images/screenshots/disable-debug-logging.gif)

## Lovelace examples

## Screenshots

