# huskium v1.1.0

This release brings significant improvements. 
Future updates will adhere to the v1.1.0 structure, 
and there will be no further updates for the v1.0.x series.

## **Stable Release**
[sphinx] https://uujohnnyuu.github.io/huskium/

## New Features
- **Page**: Timeout settings refactored, replacing the previous config.
- **Element**: Cache settings refactored, replacing the previous config.
- **Wait**: Enhanced WebDriverWait for improved efficiency.
- **Logging**: Upgraded `logging.Filter`, replacing config and logstack functionalities.
- **Exception**: Introduced `NoSuchCacheException` for simpler `cache_try` extensions.

## Enhancements  
- **Core**: Core features like `Page` and `Element` have been relocated to `core` for better management.
- **Descriptor**: Optimized data flow for timeout, cache, and wait attributes.
- **Debug**: Excessive debug logs have been removed, retaining only essential information.

## Deprecation  
- **Logstack**: Now replaced by `logfilter`.
- **Config**: Superseded by dedicated feature settings.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.1.0
```
---

# huskium v1.0.7

## **Stable Release**  

## Enhancements  
- **Cache**: Optimized cache structure and data flow with `cache_try`.  
- **Logging**: Improved configuration for `PrefixFilter` and related objects.  
- **Debug**: Enhanced debug mode for core functionalities.
- **Docstring**: Refactored all documentation to follow the Sphinx Google style format.
- **Sphinx**: https://uujohnnyuu.github.io/huskium/

## Deprecation  
- **logstack**: With the introduction of logging filters, `logstack` will be deprecated in v1.1.0+.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.7
```
---

# huskium v1.0.6

## Overview
- **Stable release**.
- **New features**: Added `log_filter` and `log_adapter` module.
- **Enhancements**: Improved `debug mode` across all functionalities.
- **Deprecation**: `logstack` will be deprecated in v1.1.0+.

## New Features
- **log_filter**: Added `PrefixFilter`, `FuncPrefixFilter`, and `FilePrefixFilter`.
- **log_adapter**: Added `PageElementLoggerAdapter`.

## Enhancements
- **Debug Mode**: Significantly improved debug mode display and functionality.

## Deprecation
- **logstack**: With the introduction of logging filters for tracking specific frames, 
`logstack` is set to be deprecated in v1.1.0+.  
As of v1.0.6, huskium's internal components no longer use `logstack`.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.6
```
---

# huskium v1.0.5

## Overview
- **Stable version**.
- **Enhancements** based on v1.0.4.

## Enhancements
- **Element Data Descriptor**: Simplified `_page` data flow.
- **Dynamic Attributes**: Simplified data flow for all dynamic attributes.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.5
```
---

# huskium v1.0.4

## Overview
- **Stable version**.
- **Enhancements** and **Bug Fixes** based on v1.0.3.

## Enhancements
- **Exception**: Optimized exception chain info to display only essential error chains.

## Bug Fixes
- **Reraise**: Fixed an issue where 
`wait_visible`, `wait_invisible`, `wait_clickable`, `wait_unclickable`, `wait_selected`, and `wait_unselected` 
would still raise a `TimeoutException` even when `reraise=False`.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.4
```
---

# huskium v1.0.3

## Overview
- **Enhancements** based on version 1.0.2.

## Enhancements
- **Type Hint**: Resolve all mypy errors except those requiring `--strict`.
- **Cache Flow**: Improved the stability of cache-related data flow.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.3
```
---

# huskium v1.0.2

## Overview
- **Enhancements** and **Bug Fixes** based on version 1.0.1.

## Enhancements
- **Type Hint**: Resolved mypy issues with `[return]` and `[return-value]`.

## Bug Fixes
- **Page**: Fixed missing return values in `supports_fedcm` and `dialog`.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.2
```
---

# huskium v1.0.1

## Overview
- **New features**, **enhancements**, and **bug fixes** based on version 1.0.0.

## New Features
- **Elements**: Added methods to retrieve multiple elements' 
`get_dom_attributes`, `shadow_roots`, `aria_roles`, and `accessible_names` in a single operation.

## Enhancements
- **Elements**: Removed unnecessary methods like `all_visible_xxx` and `any_visible_xxx`, 
leaving users to extend them as needed.
- **Dynamic Element(s)**: Eliminated redundant validation 
when assigning dynamic elements with data descriptors.
- **Log**: Removed `logconfig` and merged its functionality into `logstack`.

## Bug Fixes
- **Error Message**: Fixed error messages in validation to correctly display the expected type name.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.0.1
```
---

# huskium v1.0.0

## Overview
- Rename huskyPO to **huskium**.
- Update to Appium 4.4.0 (released on 2024/11/30).

## Installation
To install or upgrade to this version, run the following command:
```sh
pip install huskium==1.0.0
```