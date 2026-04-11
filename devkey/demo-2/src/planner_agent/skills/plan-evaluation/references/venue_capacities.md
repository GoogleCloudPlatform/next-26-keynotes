# Las Vegas Venue Capacities

Capacity data for marathon event infrastructure planning.

| Venue | Area (sq meters) | Max Capacity |
|-------|-----------------|--------------|
| Fremont Street Experience | 45,000 | 25,000 |
| Las Vegas Convention Center | 185,000 | 80,000 |
| Welcome to Las Vegas Sign | 2,000 | 1,500 |
| Bellagio Fountains | 8,000 | 5,000 |
| Caesars Palace | 15,000 | 10,000 |
| MGM Grand | 12,000 | 8,000 |
| Mandalay Bay | 18,000 | 12,000 |
| Sunset Park | 130,000 | 30,000 |
| Craig Ranch Regional Park | 95,000 | 20,000 |
| Springs Preserve | 72,000 | 15,000 |
| Symphony Park | 28,000 | 12,000 |
| Downtown Container Park | 5,000 | 3,000 |
| UNLV Campus | 65,000 | 25,000 |
| World Market Center | 45,000 | 20,000 |

## Event Type Capacity Multipliers

The needed capacity is calculated as `expected_attendance * multiplier`:

| Event Type | Multiplier | Notes |
|-----------|-----------|-------|
| marathon_start_finish | 1.0 | Full attendance at start/finish |
| water_station | 0.15 | Only a fraction of runners at any station |
| spectator_zone | 0.5 | Half the crowd at any viewing point |
| staging_area | 0.3 | Equipment and logistics crew |

## Guidelines

- Start/finish areas should ideally hold 10,000+ people
- Water stations need minimum 500 sq meters for table setup
- Utilization above 90% is a concern — recommend overflow areas
- Utilization above 100% is unacceptable — must find larger venue
