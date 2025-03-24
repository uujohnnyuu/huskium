# huskium v1.1.1

## **Stable Release**
[sphinx] https://uujohnnyuu.github.io/huskium/

## Enhancements  
- **Core**: Enhanced data flow and performance.
- **ActionChains**: Enhanced chain structure for Page and Element.

## Installation
To install or upgrade to this version, run:
```sh
pip install huskium==1.1.1
```

---

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