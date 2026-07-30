"""Project 1 — Turbojet Performance Simulator.

A station-by-station, real-cycle (non-ideal, constant-but-different
cold/hot specific heats) thermodynamic model of a single-spool turbojet,
built from standard gas-turbine cycle relations (Cohen, Rogers &
Saravanamuttoo, *Gas Turbine Theory*; Mattingly, *Elements of Gas Turbine
Propulsion*).

Modules
-------
atmosphere : International Standard Atmosphere (ISA) model.
components : Intake / compressor / combustor / turbine / nozzle physics.
engine     : ``TurbojetEngine`` — wires the components into a full cycle.
performance: Thrust, TSFC and efficiency figures of merit.
sweep      : Parametric sweeps (pressure ratio, turbine inlet temperature).
plotting   : Publication-quality performance-map figures.
"""
