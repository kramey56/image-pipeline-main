import datetime
import logging

class KLVBlock:
    """ Hold data for one KLV data record """
    def __init__(self, uid):
        self.__klv_dict = {}
        self.__klv_dict['uid'] = uid

    def __set_checksum(self, cs_val):
        self.__klv_dict['checksum'] = str(int.from_bytes(cs_val, byteorder='big', signed=False))

    def __set_time_stamp(self, ts_val):
        dv = int.from_bytes(ts_val, byteorder='big', signed=False)
        dts = datetime.datetime.utcfromtimestamp(dv/1000000)
        self.__klv_dict['time_stamp'] = dts.strftime('%Y-%m-%dT%H:%M:%S.%f UTC')

    def __set_platform_heading_angle(self, a_val):
        ra = int.from_bytes(a_val, byteorder='big', signed=False)
        self.__klv_dict['platform_heading_angle'] = str(360/65535 * ra)

    def __set_platform_pitch_angle(self, a_val):
        ra = int.from_bytes(a_val, byteorder='big', signed=True)
        self.__klv_dict['platform_pitch_angle'] = str(40/65534 * ra)

    def __set_platform_roll_angle(self, a_val):
        ra = int.from_bytes(a_val, byteorder='big', signed=True)
        self.__klv_dict['platform_roll_angle'] = str(100/65534 * ra)

    def __set_platform_designation(self, s_val):
        desig_chars = [chr(c) for c in s_val]
        self.__klv_dict['platform_designation'] = ''.join(desig_chars)

    def __set_image_source_sensor(self, s_val):
        source_chars = [chr(c) for c in s_val]
        self.__klv_dict['source_sensor'] = ''.join(source_chars)

    def __set_image_coordinate_system(self, c_val):
        coord_chars = [chr(c) for c in c_val]
        self.__klv_dict['coordinate_system'] = ''.join(coord_chars)

    def __set_sensor_latitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['sensor_latitude'] = str(180/4294967294 * lv)

    def __set_sensor_longitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['sensor_longitude'] = str(360/4294967294 * lv)

    def __set_sensor_true_altitude(self, a_val):
        av = int.from_bytes(a_val, byteorder='big', signed=False)
        self.__klv_dict['sensor_true_altitude'] = str(19900/65535 * av - 900)

    def __set_sensor_horizontal_fov(self, f_val):
        fv = int.from_bytes(f_val, byteorder='big', signed=False)
        self.__klv_dict['sensor_horizontal_fov'] = str(180/65535 * fv)

    def __set_sensor_vertical_fov(self, f_val):
        fv = int.from_bytes(f_val, byteorder='big', signed=False)
        self.__klv_dict['sensor_vertical_fov'] = str(180/65535 * fv)

    def __set_sensor_relative_azimuth_angle(self, a_val):
        av = int.from_bytes(a_val, byteorder='big', signed=True)
        self.__klv_dict['sensor_relative_azimuth_angle'] = str(360/4294967294 * av)

    def __set_sensor_relative_elevation_angle(self, a_val):
        ea = int.from_bytes(a_val, byteorder='big', signed=True)
        self.__klv_dict['sensor_relative_elevation_angle'] = str(360/4294967294 * ea)

    def __set_sensor_relative_roll_angle(self, r_val):
        rv = int.from_bytes(r_val, byteorder='big', signed=False)
        self.__klv_dict['sensor_relative_roll_angle'] = str(360/4294967294 * rv)

    def __set_slant_range(self, s_val):
        sv = int.from_bytes(s_val, byteorder='big', signed=False)
        self.__klv_dict['slant_range'] = str(5000000/4294967295 * sv)

    def __set_target_width(self, w_val):
        wv = int.from_bytes(w_val, byteorder='big', signed=False)
        self.__klv_dict['target_width'] = str(10000/65535 * wv)

    def __set_frame_center_latitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['frame_center_latitude'] = str(180/4294967294 * lv)

    def __set_frame_center_longitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['frame_center_longitude'] = str(360/4294967294 * lv)

    def __set_frame_center_elevation(self, e_val):
        ev = int.from_bytes(e_val, byteorder='big', signed=False)
        self.__klv_dict['frame_center_elevation'] = str(19900/65535 * ev - 900)

    def __set_target_location_latitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['target_location_latitude'] = str(180/4294967294 * lv)

    def __set_target_location_longitude(self, l_val):
        lv = int.from_bytes(l_val, byteorder='big', signed=True)
        self.__klv_dict['target_location_longitude'] = str(360/4294967294 * lv)

    def __set_target_location_elevation(self, e_val):
        ev = int.from_bytes(e_val, byteorder='big', signed=True)
        self.__klv_dict['target_location_elevation'] = str(19900/65535 * ev - 900)

    def __set_target_gate_width(self, w_val):
        wv = int.from_bytes(w_val, byteorder='big', signed=False)
        self.__klv_dict['target_gate_width'] = str(round(2 * wv))

    def __set_target_gate_height(self, h_val):
        hv = int.from_bytes(h_val, byteorder='big', signed=False)
        self.__klv_dict['target_gate_height'] = str(round(2 * hv))

    def __set_lds_version_number(self, v_val):
        vers = [str(v) for v in v_val]
        self.__klv_dict['lds_version_number'] = ''.join(vers)

    def __set_miis_core_identifier(self, id_val):
        self.__klv_dict['miis_core'] = '{}'.format(' '.join(hex(c) for c in id_val))

    funcMap = {
        1: __set_checksum, 2: __set_time_stamp, 5: __set_platform_heading_angle,
        6: __set_platform_pitch_angle, 7: __set_platform_roll_angle,
        10: __set_platform_designation, 11: __set_image_source_sensor,
        12: __set_image_coordinate_system,
        13: __set_sensor_latitude, 14: __set_sensor_longitude,
        15: __set_sensor_true_altitude, 16: __set_sensor_horizontal_fov,
        17: __set_sensor_vertical_fov, 18: __set_sensor_relative_azimuth_angle,
        19: __set_sensor_relative_elevation_angle, 20: __set_sensor_relative_roll_angle,
        21: __set_slant_range, 22: __set_target_width, 23: __set_frame_center_latitude,
        24: __set_frame_center_longitude, 25: __set_frame_center_elevation,
        40: __set_target_location_latitude, 41: __set_target_location_longitude,
        42: __set_target_location_elevation, 43: __set_target_gate_width,
        44: __set_target_gate_height, 65: __set_lds_version_number,
        94: __set_miis_core_identifier
    }

    def __process_record(self, key, val):
        """ Extract data from individual data records """
        try:
            self.funcMap[key](self, val)
        except KeyError:
            err_msg = f'Unknown record type: {key} data: {val}'
            logging.error(err_msg)

    def process_block(self, data, size):
        """ Extract and process indivicual data records within a KLV block """
        counter = 0
        while counter < size:
            record_id = data[counter]
            counter += 1
            cnt = data[counter]
            counter += 1
            value = data[counter:counter + cnt]
            counter += cnt
            self.__process_record(record_id, value)

        return self.__klv_dict
