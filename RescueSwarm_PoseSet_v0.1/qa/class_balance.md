# RescueSwarm Pose Dataset Class & Attribute Balance

## 1. Split Distribution

| Split | Images | Annotations | Persons/Image |
|---|---|---|---|
| train | 240 | 422 | 1.76 |
| val | 30 | 44 | 1.47 |
| test | 30 | 53 | 1.77 |
| **Total** | **300** | **519** | **1.73** |

## 2. Posture Distribution

| Posture | Count | Percentage |
|---|---|---|
| `upright` | 274 | 52.8% |
| `crouching` | 117 | 22.5% |
| `lying` | 75 | 14.5% |
| `seated` | 53 | 10.2% |

## 3. Camera View Distribution

| Camera View | Count | Percentage |
|---|---|---|
| `oblique` | 402 | 77.5% |
| `top_down` | 73 | 14.1% |
| `ground_level` | 44 | 8.5% |

## 4. Altitude Band Distribution

| Altitude Band | Count | Percentage |
|---|---|---|
| `low` | 229 | 44.1% |
| `mid` | 213 | 41.0% |
| `high` | 77 | 14.8% |

## 5. Occlusion Levels

| Occlusion | Count | Percentage |
|---|---|---|
| `none` | 336 | 64.7% |
| `partial` | 151 | 29.1% |
| `heavy` | 32 | 6.2% |

## 6. Label Source & Review Status

| Label Source | Review Status | Count | Percentage |
|---|---|---|---|
| `model_prelabel_unreviewed` | `unreviewed` | 331 | 63.8% |
| `synthetic` | `reviewed` | 188 | 36.2% |
