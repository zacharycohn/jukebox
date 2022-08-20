import soco

devices = {device.player_name: device for device in soco.discover()}
print(devices["Den"].get_current_transport_info())

