## 2. Data Sources 

### 2.1 Hot Water Data - Veitur.is API 
- **Base URL:** `https://api.veitur.is/api`
- **Documentation:** https://api.veitur.is/swagger/index.html
- **Authentication:** Bearer token (JWT) - get from Veitur "Mínar síður"

⚠️ **Important Discovery:** Readings are at **IRREGULAR intervals** (not monthly). One reading may cover 30 days, another 254 days (meter change). The app normalizes data to daily averages for fair comparison.

#### Endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/meter/info` | GET | List all your meters (hot water, cold water, etc.) |
| `/api/meter/usage-series` | GET | Hourly usage data (tímaraðir) |
| `/api/meter/reading-history` | GET | Meter readings history (álestrasaga) |

#### Parameters:
- `PermanentNumber` - Your meter's permanent number (fastanúmer)
- `DateFrom` / `DateTo` - Date range for queries

#### Response Fields (usage-series):
| Field | Description |
|-------|-------------|
| `permNumber` | Permanent meter number |
| `globalNumber` | Global meter number |
| `usageUnit` | Unit of measurement (likely m³ or liters) |
| `totalUsage` | Total usage for the period |
| `dataStatus` | 0=Success, 521=No data, etc. |
| `data[].usages[].timeStamp` | Timestamp of reading |
| `data[].usages[].value` | Usage value |

#### Data Status Codes:
- 0: Successful
- 3: Error
- 500: No A+ values
- 501-503: Missing date ranges
- 520: Meter not found
- 521: No data found

### 2.2 Electricity Data - HS Veitur API 
- **Base URL:** `https://www.hsveitur.is/umbraco/api/`
- **Endpoint:** `Expectus/UsageData`
- **Authentication:** Public token + Private token + Customer ID
- **Note:** This is a different company/API from Veitur.is (hot water)


#### Available Fields:
| Field | Description |
|-------|-------------|
| `date` | Timestamp of the reading |
| `delta_value` | Usage since last reading (kWh) |
| `index_value` | Meter reading |
| `temperature` | Temperature (unclear source) |
| `delivery_point_name` | Location/meter name |
| `unitcode` | Unit of measurement |
| `type` | Type of utility |
| `meter_id` | Unique meter identifier |

#### Info
- [x] Data granularity: **Hourly** readings
- [x] Available date range: **1+ years** historical
- [x] Rate limits: None observed

### 2.3 Weather Data - Open-Meteo API 
- **Provider:** Open-Meteo (free, no API key required)
- **Location:** Hvassaberg 10, Hafnarfjörður, Iceland
- **Coordinates:** 64.0671° N, 21.9426° W

#### Data Available:
- ✅ Outdoor temperature (hourly)
- ✅ Wind speed (km/h)
- ✅ Humidity (%)
- ✅ Historical data (via archive API)

### 2.4 EV Charging Data - Zaptec API 
- **Provider:** Zaptec (EV charger manufacturer)
- **Base URL:** `https://api.zaptec.com/api`
- **Documentation:** https://docs.zaptec.com/reference
- **Authentication:** OAuth 2.0 (username/password → Bearer token)

#### Authentication Flow:
1. POST to `https://api.zaptec.com/oauth/token` with:
   - `grant_type=password`
   - `username=<zaptec_account_email>`
   - `password=<zaptec_account_password>`
2. Returns `access_token` (expires in 3600 seconds)
3. Use `Authorization: Bearer {access_token}` for API calls

#### Key Endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chargehistory` | GET | Completed charge sessions (page size: 50-100) |
| `/api/chargers` | GET | List of chargers |
| `/api/installation` | GET | Installation info |

