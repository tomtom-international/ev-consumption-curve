#! /usr/bin/env python3

# Copyright (C) 2023 TomTom NV.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
import sys
import textwrap
from dataclasses import dataclass
from typing import Tuple, Optional

if sys.version_info < (3, 7):
    sys.exit("This script requires Python 3.7 or later.")


def air_density(temperature: float) -> float:
    """
    Air density (mass per unit volume) at a given temperature, in kg/m³.
    We're using the ideal gas law: rho = P / (R * T), where P is the pressure,
    R is the specific gas constant, and T is the temperature in Kelvin.
    """

    # Standard atmospheric pressure at sea level, in Pascal (N/m²).
    ATMOSPHERIC_PRESSURE = 101325
    # Specific gas constant for dry air, in J/(K·kg).
    SPECIFIC_GAS_CONSTANT = 287.053
    # 0°C in Kelvin.
    ZERO_CELSIUS_IN_KELVIN = 273.15

    return ATMOSPHERIC_PRESSURE / (
        SPECIFIC_GAS_CONSTANT * (ZERO_CELSIUS_IN_KELVIN + temperature)
    )


def kmh_to_meters_per_second(speed_kmh: float) -> float:
    speed_ms = speed_kmh * (1000 / 3600)
    return speed_ms


@dataclass(frozen=True)
class Vehicle:
    # We use MKS units unless specified otherwise.
    mass: float  # kg
    drag_area: float  # m²
    drivetrain_efficiency: float  # dimensionless
    rolling_resistance_coeff: float  # dimensionless
    idle_power: float  # Watt

    def _rolling_resistance_force(self) -> float:
        STANDARD_GRAVITY = 9.81  # gravity on Earth's surface in m/s²
        normal_force = self.mass * STANDARD_GRAVITY
        return self.rolling_resistance_coeff * normal_force

    def _air_drag_force(self, speed: float, temperature: float) -> float:
        return 0.5 * air_density(temperature=temperature) * self.drag_area * speed ** 2

    def _idle_power_force(self, speed: float) -> float:
        return self.idle_power / speed  # 1 W = 1 N·m / s

    def _total_force(self, speed: float, temperature: float) -> float:
        return (
            self._rolling_resistance_force()
            + self._air_drag_force(speed=speed, temperature=temperature)
        ) / self.drivetrain_efficiency + self._idle_power_force(speed=speed)

    def consumption_in_kWh_per_100km(self, speed_kmh: float, temperature: float) -> float:
        """
        Energy consumption in kWh/100km for a given speed (km/h) and temperature (°C).
        """
        speed_ms = kmh_to_meters_per_second(speed_kmh)
        # 1 N = 1 Ws / m = (100 / 3600) · (kWh / 100km)
        NEWTON_TO_KWH_100KM = 100 / 3600
        return self._total_force(speed=speed_ms, temperature=temperature) * NEWTON_TO_KWH_100KM


@dataclass(frozen=True)
class Params:
    vehicle: Vehicle
    temperature: float
    highway_consumption: Optional[float]
    max_speed: int


def parse_params() -> Params:
    def valid_range(min_value, max_value):
        def check_valid_range(value):
            fvalue = float(value)
            if fvalue < min_value or fvalue > max_value:
                raise argparse.ArgumentTypeError(
                    f"Value must be between {min_value} and {max_value}."
                )
            return fvalue

        return check_valid_range

    DEFAULT_LOAD_WEIGHT = 90
    DEFAULT_DRAG_COEFFICIENT = 0.27

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            Calculate consumption curve from physical parameters of an electric car.
            The consumption curve is used in the TomTom routing API (constantSpeedConsumptionInkWhPerHundredkm), see
            https://developer.tomtom.com/routing-api/documentation/routing/common-routing-parameters .
            The consumption curve indicates the consumption of the car at a given constant speed on a flat surface.
            It is represented as "speed1:consumption1,speed2:consumption2,...", with speed in km/h and consumption in kWh/100km.

            Recommended usage:
            * Specify the curb weight.
            * Specify the drag area.
              * If the drag area is not available, specify drag coefficient and frontal area.
                * If frontal area is not available, specify width and height.
            * Consider specifying rolling resistance coefficient, drivetrain efficiency, and idle power, if information on them is available.
            * Consider using different consumption curves for different temperatures.

            Example:
            consumption-curve.py --curb-weight=1812 --width=1.805 --height=1.570
            """
        ),
    )
    parser.add_argument(
        "--weight",
        type=valid_range(200, 80_000),
        help="Total vehicle weight (kg), including passengers and load, typically 1400–2300.",
    )
    parser.add_argument(
        "--curb-weight",
        type=valid_range(200, 80_000),
        help="Vehicle curb weight (kg), typically 1300–2200."
        f" Calculation assumes an extra load weight of {DEFAULT_LOAD_WEIGHT}kg.",
    )
    parser.add_argument(
        "--drag-area",
        type=valid_range(0.1, 4.0),
        help=f"Drag area (CdA, m²), typically 0.4–1.0.",
    )
    parser.add_argument(
        "--drag-coefficient",
        type=valid_range(0.03, 5.0),
        help=f"Drag coefficient (Cd, dimensionless), typically 0.2–0.4. Default: {DEFAULT_DRAG_COEFFICIENT}.",
    )
    parser.add_argument(
        "--frontal-area",
        type=valid_range(0.5, 8.0),
        help="Frontal area (m²), typically 2.0–2.7.",
    )
    parser.add_argument(
        "--width", type=valid_range(0.5, 4.0), help="Width (m), typically 1.7–2.0."
    )
    parser.add_argument(
        "--height", type=valid_range(0.5, 4.0), help="Height (m), typically 1.4–1.8."
    )
    parser.add_argument(
        "--rolling-resistance-coefficient",
        type=valid_range(0.003, 0.05),
        help="Rolling resistance coefficient (dimensionless), typically 0.007–0.013. Default: %(default)s.",
        default=0.01,
    )
    parser.add_argument(
        "--drivetrain-efficiency",
        type=valid_range(0.0, 1.0),
        help="Drivetrain efficiency coefficient (dimensionless), typically 0.8–0.95. Default: %(default)s.",
        default=0.9,
    )
    parser.add_argument(
        "--idle-power",
        type=valid_range(0.0, 6.0),
        help="Idle power (kW), typically 0.5–1.5. Default: %(default)s.",
        default=0.5,
    )
    parser.add_argument(
        "--highway-consumption",
        type=valid_range(50, 1000),
        help="Consumption at 110km/h at 23°C, without auxiliary consumption like A/C, in Wh/km."
        " If given, this will be used to scale the calculated curve such that the point at 110 km/h"
        " matches the given value. Typically 150–300.",
    )
    parser.add_argument(
        "--temperature",
        type=valid_range(-90, 60),
        help="Temperature (°C), typically −15–35. Default: %(default)s.",
        default=20,
    )
    parser.add_argument(
        "--max-speed",
        type=valid_range(20, 250),
        help="Maximum speed (km/h). Default: %(default)s.",
        default=200,
    )
    args = parser.parse_args()

    if not (args.weight or args.curb_weight):
        parser.error("Need either --weight or --curb-weight.")
    if args.weight and args.curb_weight:
        parser.error("Cannot have both --weight and --curb-weight.")
    if args.drag_area and any(
        (args.drag_coefficient, args.frontal_area, args.width, args.height)
    ):
        parser.error(
            "If --drag-area is given, cannot use --drag-coefficient, --frontal-area, --width, or --height."
        )
    if args.frontal_area and any((args.width, args.height)):
        parser.error("If --frontal-area is given, cannot use --width or --height.")
    if (args.width is None) != (args.height is None):
        parser.error("Both --width and --height must be given together.")

    if not args.weight:
        args.weight = args.curb_weight + DEFAULT_LOAD_WEIGHT

    if not args.drag_coefficient:
        args.drag_coefficient = DEFAULT_DRAG_COEFFICIENT

    if args.drag_area:
        pass
    elif args.frontal_area:
        args.drag_area = args.drag_coefficient * args.frontal_area
    elif args.width:
        # Compensate for frontal area not being a rectangle.
        # The factor of 0.8 was proposed in "Prediction of vehicle reference frontal area", https://www.osti.gov/biblio/6602653
        FRONTAL_AREA_FACTOR = 0.8
        frontal_area = FRONTAL_AREA_FACTOR * args.width * args.height
        args.drag_area = args.drag_coefficient * frontal_area
    else:
        parser.error("Must specify --drag-area or --frontal-area or --width and --height.")

    vehicle = Vehicle(
        mass=args.weight,
        drivetrain_efficiency=args.drivetrain_efficiency,
        rolling_resistance_coeff=args.rolling_resistance_coefficient,
        drag_area=args.drag_area,
        idle_power=1000 * args.idle_power,
    )

    # Wh/km -> kWh/100km
    highway_consumption = (
        None if args.highway_consumption is None else (args.highway_consumption / 1000) * 100
    )
    return Params(
        vehicle=vehicle,
        temperature=args.temperature,
        highway_consumption=highway_consumption,
        max_speed=int(args.max_speed),
    )


def main():
    params = parse_params()

    if params.highway_consumption:
        scaling_factor = (
            params.highway_consumption
            / params.vehicle.consumption_in_kWh_per_100km(speed_kmh=110, temperature=23)
        )
    else:
        scaling_factor = 1.0

    MIN_SPEED = 10
    SPEED_STEP = 10
    SPEEDS = range(MIN_SPEED, params.max_speed + 1, SPEED_STEP)
    curve = [
        (
            speed,
            scaling_factor
            * params.vehicle.consumption_in_kWh_per_100km(
                speed_kmh=speed, temperature=params.temperature
            ),
        )
        for speed in SPEEDS
    ]
    print(":".join(f"{s},{c:.2f}" for (s, c) in curve))


if __name__ == "__main__":
    main()
