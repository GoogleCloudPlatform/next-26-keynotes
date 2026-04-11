# Marathon Planning Guide

This guide provides essential standards and constraints for designing city-scale marathon events.

## 1. Route Standards
- **Official Distance**: 42.195 km (26.219 miles).
- **Certification**: Routes must be measured within 0.1% accuracy.
- **Course Types**: 
    - **Loop**: Start/Finish at same location (logistically simplest).
    - **Point-to-Point**: Different start/finish (requires runner shuttles).
- **Elevation**: Fast courses should limit total gain to < 300 ft. Avoid steep hills after mile 20.

## 2. Road & Traffic Infrastructure
### Road Width Requirements
| Participant Count | Minimum Width | Lanes Needed |
|-------------------|---------------|--------------|
| < 5,000           | 20 ft         | 2 lanes      |
| 5,000 - 15,000    | 30 ft         | 3 lanes      |
| 15,000 - 30,000   | 40 ft         | 4 lanes      |
| > 30,000          | 50+ ft        | 5+ lanes     |

### Traffic Impact Severity
Total closure hours = (Number of waypoints) × (Closure hours per waypoint).
- **> 40k runners**: 4.0 hrs/waypoint (Critical disruption).
- **10k - 20k runners**: 2.5 hrs/waypoint (Medium disruption).

## 3. Runner Logistics
- **Hydration**: Water stations every 3 km (standard) or every 1.5 miles.
- **Medical**: Stations at the halfway point (21.1 km) and the finish line.
- **Safety**: Ensure 10-foot corridors for emergency vehicle access.

## 4. Notable Landmarks (Las Vegas Network)
When using the `plan_marathon_route` tool, you can specify a `theme_sequence` using these supported landmark names:
- Mandalay Bay
- Luxor
- Excalibur
- New York
- MGM Grand
- Belagio (Note: spelled with one 'l' in network data)
- Caesars Palace
- Flamingo
- LINQ
- Harrahs
- Venetian
- Palazzo
- Wynn
- Encore
- Stratosphere
- Fremont Street
