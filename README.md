# TomTom EV consumption curve calculator
## Summary

This is a Python script that estimates the constant speed consumption
curve of an electric vehicle (EV) using various physical parameters.

It is for you if you want to use TomTom's [generic routing API](https://developer.tomtom.com/routing-api/documentation/routing/calculate-route) or the dedicated [long-range EV routing API](https://developer.tomtom.com/routing-api/documentation/extended-routing/long-distance-ev-routing) but don't know
how to set the [`constantSpeedConsumptionInkWhPerHundredkm`](https://developer.tomtom.com/routing-api/documentation/routing/common-routing-parameters#the-electric-consumption-model) parameter.

The script requires Python 3.7 but does not have any other dependencies.

## Introduction

This repository is useful for users of [TomTom's routing
API](https://developer.tomtom.com/routing-api/documentation/product-information/introduction)
for an electric vehicle who want to use one of these features:

* Calculating range along the route;
* Calculating the reachable range;
* Automatically adding charging stops.

These features require to give parameters describing the consumption
of the vehicle. One of these parameters is
`constantSpeedConsumptionInkWhPerHundredkm`. This specifies the
speed-dependent component of consumption (that is, ignoring
acceleration, slope, and auxiliary consumption). The parameter
specifies a list of speed/consumption rate pairs, between which the
consumption rate is linearly interpolated.

Ideally, the constant speed consumption curve is obtained by
measurements of the actual consumption. If this data is not available,
this repository can help. It provides a script
`ev-consumption-curve.py` that estimates the constant speed
consumption curve from static physical parameters of the vehicle which should
be more readily available.

## Quick start

Specify curb weight, width, and height of the vehicle.

Example:

```shell
# ./ev-consumption-curve.py --curb-weight=1812 --width=1.805 --height=1.570
10,10.85:20,8.61:30,8.22:40,8.41:50,8.95:60,9.75:70,10.77:80,12.00:90,13.42:100,15.04:110,16.83:120,18.81:130,20.98:140,23.32:150,25.84:160,28.54:170,31.42:180,34.47:190,37.70:200,41.11
```

The format is "speed1:consumption1,speed2:consumption2,...", with
speed in km/h and consumption in kWh/100km. This curve can be directly
used for the `constantSpeedConsumptionInkWhPerHundredkm` parameter of
the TomTom routing API.

Note that this will give you only a rough estimation of the constant
speed consumption curve.

## Technical terms

*Drag Coefficient (Cd):* The drag coefficient is a dimensionless
quantity that quantifies how much air resistance the vehicle's
shape produces when it's moving. The lower the drag coefficient, the
more aerodynamic (and therefore efficient) the vehicle is.

*Frontal Area:* The frontal area (also cross-sectional area) of a
vehicle is the area of the vehicle's front-facing surface. A larger
frontal area means a greater surface area is pushing against the air
as the vehicle moves, leading to higher drag and, consequently,
increased energy consumption.

*Drag Area (CdA)*: The drag area is the product of the drag
coefficient and the frontal area of the vehicle. It's a measure of the
total drag (air resistance) the vehicle will experience when in
motion.

*Rolling Resistance Coefficient (Crr):* The rolling resistance
coefficient is a measure of the force resisting the motion when a
wheel rolls on a surface. It depends on factors like the type of tire,
tire pressure, and the nature of the surface.

*Drivetrain Efficiency:* Drivetrain efficiency is a measure of how
effectively an electric vehicle's drivetrain (the group of components
that deliver power to the driving wheels) converts energy from the
battery into movement. This is less than 100% because some energy is
converted to heat due to factors like mechanical friction or electrical
resistance.

*Idle Power:* Idle power is the power an electric vehicle needs to
stay functional, independent of the speed. This is mainly the power
needed to cool the batteries. This should not include power use
unrelated to the drivetrain, such as air conditioning or the
infotainment system; those should be specified in the API with
`auxiliaryPowerInkW`.

## Usage

To get the best results, the following parameters should be specified:

* `--weight`: Total vehicle weight (kg), including passengers and load.
* `--drag-area`: Drag area (CdA, m²).
* `--rolling-resistance-coefficient`: Rolling resistance coefficient (dimensionless).
* `--drivetrain-efficiency`: Drivetrain efficiency coefficient (dimensionless).
* `--idle-power`: Idle power (kW).
* `--temperature`: Temperature (°C).

If any of the last four are not available, they can be omitted to use
the defaults instead, which are fitting for passenger cars.

If the drag area is not available, a series of increasingly rough
approximations can be made:

* If the drag coefficient is known or can be estimated, it should be
  specified with `--drag-coefficient`; otherwise a default is used.
  If the vehicle is not a regular passenger car (e.g. a truck, pickup,
  or scooter), at least an estimate should be provided here because
  the default will be unrealistic.
* If the frontal area is known, it should be specified with
  `--frontal-area`.
* Otherwise, `--width` and `--height` should be specified. The frontal
area is then estimated as 0.8 · width · height.

## How it works

The script calculates

* the force needed to overcome air resistance based on the shape of
the vehicle and the temperature; and
* the force needed to overcome rolling resistance based on the weight.

We have then the consumption for speed *v*:

airDragForce(*v*) = 0.5 · airDensity(temperature) · dragArea · *v*²

rollingResistanceForce = rollingResistanceCoefficient · 9.81 m/s² · weight

consumption(*v*) = (rollingResistanceForce + airDragForce(*v*)) / drivetrainEfficiency + idlePower/*v*

## Limitations

The calculation makes a number of simplifying assumptions, e.g.

* drivetrain loss and idle power are independent of speed;
* idle power is independent of temperature (ignoring battery cooling/heating);
* rolling resistance is independent of speed;
* rolling resistance is linear in the weight.

Thus, the result can only be an approximation of the true consumption.

## Bug reports, feature requests, and other feedback

If you encounter any problems with this script or would like to contact the
maintainers, please don't hesitate to file a GitHub issue.

## Contributions

We welcome contributions from everyone. If you have any ideas for enhancements
or bug fixes, feel free to make a pull request or open an issue.

## Maintainers

- [Marianne Guillet](https://github.com/marianneguillet-tomtom)
- [Falk Hüffner](https://github.com/FalkHueffner-TomTom)
- [Severin Strobl](https://github.com/severinstrobl-tomtom)

## License

This script is provided under the MIT license; see [LICENSE](./LICENSE) for
details.
