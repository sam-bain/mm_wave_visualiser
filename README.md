# mm_wave_visualiser
Python visualiser for mmwave radar measurement data using matplotlib tools.

This visualiser relies on a forwarding program operating on the drone companion computer in order to translate the droneCAN proximity sensor message into a MAVLINK message which is then forwarded onto the LCM bus for ground side access.

It also uses a custom lightweight MAVLINK message, SHORT_RADAR_TELEM, as opposed to the stanard OBSTACLE_DISTANCE_3D message, in order to increase the available message bandwidth. This requires a custom pymavlink compilation to run (instructions [here](https://ardupilot.org/dev/docs/code-overview-adding-a-new-mavlink-message.html)). The message definition is included below.

<message id="11045" name="SHORT_RADAR_TELEM">
    <description>Condensed radar telemetry.</description>
    <field type="uint8_t" name="sensor_id">Sensor ID.</field>
    <field type="int16_t" name="yaw" units="ddeg">Yaw to Obstacle.</field>
    <field type="int16_t" name="pitch" units="ddeg">Pitch to Obstacle.</field>
    <field type="int16_t" name="distance" units="cm">Distance to Obstacle.</field>
</message>
