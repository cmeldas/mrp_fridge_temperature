# MRP Fridge Temperature

An Odoo module for tracking and managing fridge temperatures in manufacturing environments, with Home Assistant integration for automated temperature logging.

## Overview

This module extends Odoo's Manufacturing (MRP) functionality to help you monitor and maintain proper refrigeration temperatures. It's particularly useful for businesses that need to comply with food safety regulations, pharmaceutical storage requirements, or any manufacturing process requiring temperature-controlled storage.

## Features

- **Fridge Management**: Register and manage multiple refrigeration units
- **Automated Temperature Logging**: Integration with Home Assistant for automatic temperature recording
- **High Temperature Alerts**: Configurable alerts when temperatures exceed safe thresholds
- **Multi-attempt Verification**: Reduces false alarms by verifying high temperatures over multiple checks

## Installation

### Odoo Module

1. Clone this repository into your Odoo addons directory:
2. Search for "MRP Fridge Temperature" and install the module

### Requirements

- Odoo 20.0 (branch `20.0`; `master` = Odoo 18, `19.0` = Odoo 19)
- `mrp` module (Manufacturing)

> This module does not really require any `mrp` dependencies, but it does not make sence for me to create completely new app for the Odoo.

## Home Assistant Integration

This module includes a Home Assistant blueprint (`odoo_fridge_yaml`) that automates temperature logging from your smart temperature sensors to Odoo.

### Quick Import

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Fcmeldas%2Fmrp_fridge_temperature%2Fmaster%2Fodoo_fridge_yaml)

Click the badge above to import the blueprint directly into your Home Assistant instance.

### Prerequisites

- Home Assistant instance with temperature sensors
- Odoo instance accessible from Home Assistant network
- Odoo user with API access (API keys recommended)

### Setup

1. **Configure REST Command in Home Assistant**

   Add the following to your `configuration.yaml`:

   ```yaml
   rest_command:
     odoo_api:
       url: "{{ url }}"
       method: POST
       headers:
         Content-Type: "application/json"
       payload: "{{ payload }}"
   ```

2. **Import the Blueprint**

   - Copy the contents of `odoo_fridge_yaml` file
   - In Home Assistant, go to Settings > Automations & Scenes > Blueprints
   - Click "Import Blueprint" and paste the content

3. **Create Automation from Blueprint**

   Configure the following parameters:

   - **Odoo URL**: Your Odoo instance URL (e.g., `http://localhost:8069`)
   - **Odoo Database**: Database name
   - **Odoo Login**: Username for API access
   - **Odoo Password**: Password or API key (API keys recommended for security)
   - **Fridge ID**: The ID of the fridge in Odoo (found in the fridge record)
   - **Temperature**: Template to get temperature from your sensor (e.g., `{{states('sensor.fridge_temperature')}}`)
   - **Temperature Threshold**: Temperature limit for alerts (default: 8°C)
   - **Attempts**: Number of verification attempts before alerting (default: 40)
   - **Delay Duration**: Minutes between verification attempts (default: 6)
   - **Log Time**: Daily time to log temperature (default: 04:00:00)

### How It Works

1. **Daily Logging**: At the configured time, the automation reads your temperature sensor
2. **Temperature Check**: If temperature exceeds the threshold, it waits and retries
3. **Alert**: After maximum attempts with high temperature, creates a persistent notification
4. **Log to Odoo**: Authenticates with Odoo and creates a temperature record

## Usage

### In Odoo

1. **Create a Fridge**:

   - Navigate to Manufacturing > Configuration > Fridges
   - Click "Create" and enter fridge details (name, location, etc.)
   - Note the fridge ID for Home Assistant configuration

2. **View Temperature Logs**:

   - Go to Manufacturing > Fridge Temperatures
   - Filter by fridge, date range, or temperature
   - Export data for compliance reporting

3. **Manual Temperature Entry**:
   - Click "Create" in the Temperature view
   - Select the fridge and enter temperature
   - System automatically timestamps the entry

## Odoo 20

Větev `20.0`, verze `20.0.1.0.0`. Modely, pole a pohledy se nemění.

- **Přístupová práva:** Odoo 20 nahradilo `ir.model.access` a `ir.rule` jedním modelem
  `ir.access`. Soubor `security/ir.model.access.csv` je nahrazen `security/ir.access.csv`
  (sloupce `id,name,model_id,group_id/id,operation,domain`, model se zapisuje technickým
  jménem, práva jako `crud`). Obsah je stejný: skupina Výroba / Uživatel
  (`mrp.group_mrp_user`) má plný přístup k lednicím i záznamům teplot, XML ID zůstala.
- **Home Assistant:** volání z blueprintu `odoo_fridge_yaml` (`/jsonrpc`, `common.login`,
  `object.execute_kw` → `mrp.fridge.temperature.create` s `fridge_id` a `temperature`) funguje
  v 20 beze změny (s heslem nebo s API klíčem se scope `rpc`, viz níže); ověřuje to test `test_home_assistant_blueprint_calls`. Endpoint `/jsonrpc`
  je od 19 označený jako zastaralý (zrušení plánuje Odoo ve verzi 22) a při každém volání zapíše
  do logu varování. Před přechodem na 22 bude potřeba blueprint přepsat na `/json/2`
  s API klíčem.
- **API klíč pro Home Assistant:** Odoo 20 přijímá pro RPC jen API klíče se scope `rpc`
  (`_check_apikey_credentials` hledá `scope = 'rpc'`, v 19 bylo `scope IS NULL OR …`).
  Globální klíč vytvořený v 19 (scope prázdný) se v 20 nepřihlásí a blueprint by přestal
  zapisovat teploty bez viditelné chyby v Odoo. Na produkci je to přesně klíč
  „Homeassistant“ uživatele s id 2. Migrace modulu proto klíče s prázdným scope převede
  na `rpc` (viz Migrace dat níže), HA pak funguje se stávajícím klíčem. Ověřuje to test
  `test_home_assistant_api_key_scope` (klíč s `NULL` se nepřihlásí, po migraci ano).
- Nově jsou v `tests/` testy (překročení limitu, přístupová práva, volání jako z HA).

### Migrace dat (19 → 20)

`migrations/20.0.1.0.0/pre-migrate.py` před aktualizací modulu smaže z `ir_model_data` XML ID
modulu, která v databázi z 19 ukazují ještě na `ir.model.access` (na produkci
`access_mrp_fridge_user` a `access_mrp_fridge_temperature_user`). Bez toho by načtení
`ir.access.csv` se stejnými XML ID spadlo na „found record of different model“ (ověřeno).
CSV pak založí nové záznamy `ir.access`. Pokud XML ID už dřív převedla obecná migrace jádra
na `ir.access`, skript nic nedělá. Staré řádky `ir_model_access` zůstávají.

Stejný skript pak převede API klíče s prázdným scope (globální klíče z 19) na scope `rpc`:
`UPDATE res_users_apikeys SET scope = 'rpc' WHERE scope IS NULL`. V 20 by se takový klíč
nepřihlásil nikam, `rpc` odpovídá tomu, co uměl v 19. Na produkci (6. 10. 2026) je to jediný
klíč „Homeassistant“, který používá blueprint. Úprava je nezávislá na jádru; když ji
udělá i obecná migrace `base`, skript už nic nenajde.

Vlastní data (`mrp_fridge`: 6 lednic, `mrp_fridge_temperature`: 1 964 záznamů na produkci
6. 10. 2026) migraci nepotřebují.

## License

This module is licensed under LGPL-3.
