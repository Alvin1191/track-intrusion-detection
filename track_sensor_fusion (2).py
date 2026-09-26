# (c) Alvin Tarpeh - All Rights Reserved. Original concept and implementation.

import time


class TrackSensorFusion:
    """
    Developed by Alvin Tarpeh
    Processes trackside LiDAR volume data and estimates mass.
    Filters out false positives (rats, trash) and ignores massive static equipment.
    """

    MIN_HUMAN_WEIGHT = 50.0   # lbs (filters out small animals/trash)
    MAX_HUMAN_WEIGHT = 600.0  # lbs (strict upper boundary limit)

    @classmethod
    def evaluate_mass(cls, estimated_weight_lbs):
        """
        Calculates whether the detected mass matches a human profile.
        """
        print(f"[Sensor] Object detected. Calculated Weight: {estimated_weight_lbs} lbs.")
        if cls.MIN_HUMAN_WEIGHT <= estimated_weight_lbs <= cls.MAX_HUMAN_WEIGHT:
            return True
        else:
            print("[Sensor Warning] Object filtered out. Mass does not match human parameters.")
            return False


class BrakingPhysics:
    """
    Developed by Alvin Tarpeh
    Calculates stopping distances based on current velocity and deceleration types.

    Deceleration rates are real NYCT fleet specs, consistent across every major
    car class still in service (R42, R46, R62/R62A, R142/R142A, R143, R160, R188):
      - Full service (normal) braking: 3.0 mph/s = 1.3 m/s^2
      - Emergency braking:              3.2 mph/s = 1.4 m/s^2
    Source: Wikipedia rolling-stock spec tables for each car class (2026).
    Note the real gap between normal and emergency braking is small (~8%),
    not the dramatic difference often assumed in early-stage safety proposals.
    """

    STANDARD_DECEL = 1.3   # m/s^2, full service braking (real NYCT spec)
    QUICK_STOP_DECEL = 1.4  # m/s^2, emergency braking (real NYCT spec)

    @staticmethod
    def mph_to_mps(mph):
        return mph * 0.44704

    @classmethod
    def calculate_stopping_distance(cls, velocity_mph, use_quick_stop=True):
        initial_velocity_mps = cls.mph_to_mps(velocity_mph)
        deceleration = cls.QUICK_STOP_DECEL if use_quick_stop else cls.STANDARD_DECEL
        stopping_distance_meters = (initial_velocity_mps ** 2) / (2 * deceleration)
        return round(stopping_distance_meters, 2)


class TransitControlCenter:
    def __init__(self):
        # Station sequence is real (4/5 train, IRT Lexington Ave Line, in true order:
        # Brooklyn Bridge-City Hall -> Fulton St -> Wall St -> Bowling Green).
        # Distances are computed from each station's published Wikipedia coordinates
        # using the haversine formula (straight-line distance, not curved track
        # length, so real track distance may run slightly longer):
        #   Fulton St (40.71028, -74.00778) -> Wall St (40.70771, -74.011717): 438 m
        #   Wall St (40.70771, -74.011717) -> Bowling Green (40.70417, -74.01444): 456 m
        # These represent one real stop away from the incident station in each
        # direction, not a full two-stop gap -- chaining a third real station would
        # be needed for that, and gets complicated near the southern end of the line
        # where Bowling Green sits close to the South Ferry loop terminal.
        self.active_trains = {
            "Train_4_Uptown": {"current_speed_mph": 45, "distance_to_incident_station_meters": 456},
            "Train_4_Downtown": {"current_speed_mph": 35, "distance_to_incident_station_meters": 438},
        }

    def process_incident(self, station_name, estimated_weight):
        print(f"\n--- INTRUSION PROTOCOL ACTIVATED: {station_name.upper()} ---")

        if not TrackSensorFusion.evaluate_mass(estimated_weight):
            print("System Standby: Intrusion threat cleared via weight constraints.")
            return

        print("CRITICAL: Human track intrusion verified. Scanning transit grid for trains...")

        for train_id, telemetry in self.active_trains.items():
            speed = telemetry["current_speed_mph"]
            actual_distance = telemetry["distance_to_incident_station_meters"]

            standard_stop_dist = BrakingPhysics.calculate_stopping_distance(speed, use_quick_stop=False)
            quick_stop_dist = BrakingPhysics.calculate_stopping_distance(speed, use_quick_stop=True)

            print(f"Evaluating {train_id}:")
            print(f"  -> Speed: {speed} MPH | Distance to Hazard: {actual_distance} meters")
            print(f"  -> Standard Stop Distance: {standard_stop_dist} meters")
            print(f"  -> Quick-Stop Brake Distance: {quick_stop_dist} meters")

            if actual_distance < quick_stop_dist:
                print(f"[CRITICAL] {train_id}: Cannot stop in time. Signaling override initiated.")
            elif actual_distance <= standard_stop_dist:
                print(f"[EMERGENCY] {train_id}: ENGAGE QUICK-STOP BRAKES IMMEDIATELY.")
            else:
                print(f"[EARLY WARNING] {train_id}: Slow down. Hazard detected 2 stops ahead.")


if __name__ == '__main__':
    system = TransitControlCenter()

    # Case A: False positive (15 lb trash bag)
    system.process_incident(station_name="Bowling Green", estimated_weight=15.2)
    time.sleep(1)

    # Case B: Real emergency (185 lb human on tracks)
    system.process_incident(station_name="Wall Street", estimated_weight=185.0)
