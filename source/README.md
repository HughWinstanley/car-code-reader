# Car Code Reader

A desktop app that plugs into your car's OBD-II port (through an adapter) and:

- **Reads engine/transmission codes**: stored, pending and permanent. Works on any car sold in the US from 1996 on.
- **Scans other modules** like ABS/brakes, airbags, body control and the instrument cluster. Works on most CAN cars (roughly 2008 and newer).
- Explains every code in plain English, with common causes, and searches online with a double-click.
- **Clears codes** and turns off the check-engine light. It warns you about what that resets first.
- Shows **live sensor data**, the **freeze frame**, **emissions readiness** (smog-check status), the **VIN** and battery voltage.
- Saves a text **report** you can take to a mechanic.
- Has **Demo modes** (a modern car and a 2004 GM truck) so you can try everything before you buy an adapter.

## 1. Get an adapter

To read the most codes, get an **OBDLink** adapter. They support every OBD-II protocol and the extra Ford and GM networks, and they behave reliably. Cheap no-name "ELM327 v2.1" clones often miss modules or drop out.

| Adapter | Connects by | Good for |
|---|---|---|
| **OBDLink EX** | USB cable | Windows laptops. Cheapest reliable option, and supports Ford MS-CAN. |
| **OBDLink MX+** | Bluetooth | Windows, Android or a laptop with no cable. Supports Ford MS-CAN and GM SW-CAN. |
| Any ELM327 clone | USB, Bluetooth or Wi-Fi | Fine for engine codes. Hit-or-miss for ABS and airbag codes. |

Avoid "BLE"-only adapters (Bluetooth Low Energy, often sold "for iPhone"). They don't show up as a port on a computer.

## 2. Install on a Mac (the app)

1. Install **Python 3** from <https://www.python.org/downloads/macos/> if you don't have it. It's a normal installer; just click through. (If you skip this, the app tells you and opens that page.)
2. Unzip **Car-Code-Reader-Mac.zip** and drag **Car Code Reader** into your **Applications** folder.
3. The first time, macOS will block it because it isn't from the App Store or a registered developer. Double-click it once, click **Done**, then go to **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to "Car Code Reader". You only do this once.

Mac notes:
- **USB adapters work best on a Mac.** They show up as `/dev/cu.usbserial-…`. Wi-Fi adapters also work (join the adapter's Wi-Fi first). Recent macOS versions are unreliable with classic Bluetooth OBD adapters.
- The menu bar shows "Python" while the app runs. That's normal for this kind of app.
- If something goes wrong, there's a log at `~/Library/Logs/Car Code Reader.log`.

## 2b. Install on Windows or Linux

1. Install **Python 3** from <https://www.python.org/downloads/>. On Windows, tick **"Add Python to PATH"** during setup.
   *(Linux only: also run `sudo apt install python3-tk`.)*
2. Put `car_code_reader.py`, `obd_core.py`, `dtc_database.py`, `icons.py`, `vehicles.py` and `icon.png` in the same folder.
3. Open a terminal (Windows: Command Prompt) in that folder and run:
   ```
   pip install pyserial
   python car_code_reader.py
   ```
   On Mac/Linux, use `pip3` and `python3`.

## 3. Use it

1. Plug the adapter into the OBD port under the dashboard, near the steering column, and turn the key to **ON**.
2. Open the app and click **Connect**. It finds the adapter by itself and scans straight away.
3. The warning lamp and headline tell you how things stand. Each problem shows how urgent it is (**Fix soon**, **Get it checked**, **Low priority**, **Past problem**). Click one to see why it matters and what usually fixes it.
4. **Clear codes** turns the warning lights off once a repair is done. Turn the engine off and leave the key on first.

The pages on the left:
- **Problems**: the scan results.
- **Live data**: engine readings in real time, plus the freeze frame (a snapshot from when the check-engine light came on).
- **Smog check**: whether the vehicle is ready for an emissions inspection.
- **Vehicle**: year, make, VIN and battery voltage.
- **Help**: quick steps, and the adapter log if something needs troubleshooting.

No adapter yet? On the first screen, click **2012 Ford** or **2004 GM truck** to try everything with a pretend vehicle. If the automatic search can't find your adapter, open **Connection options** and pick the port yourself.

## Semi trucks and 1995-and-older vehicles

- **Semi trucks (heavy-duty, J1939, about 2007 and newer):** click **Semi trucks** on Home. You need a
  9-pin Deutsch to OBD-II cable (green 9-pin on 2016+ trucks). The app reads active and previously
  active codes from every module (engine, transmission, ABS, aftertreatment...), shows live engine data,
  and can clear codes. The OBDLink EX is for 12-volt systems, which covers most US trucks.
- **1995 and older (OBD-I):** click **1995 and older** on Home (or pick a pre-1996 vehicle). The app walks
  you through making the check-engine light blink the codes for GM, Ford/Lincoln/Mercury,
  Chrysler/Dodge/Jeep/Plymouth, Toyota/Lexus and Honda/Acura; type in what you count and it explains them.
  No adapter needed.
- Not covered: pre-2007 semis on the older J1708 network, OBD-I ABS/airbag codes, and reading GM ALDL data
  with a cable.

## Honest limits

- **Engine codes** are standardized and work on every 1996+ car.
- **ABS, airbag and body codes** — what's covered for Ford and Chevy/GM:
  - **GM about 1996–2006** (Class 2), e.g. 2004 Silverado: well documented, solid.
  - **GM about 2007–2016** (GMLAN, e.g. GMT900 and early K2 trucks): uses GM's own published method. Modules on GM's single-wire network (some radio/body modules) can't be reached with the OBDLink EX.
  - **GM 2017+** and other newer cars: the standard (UDS) method.
  - **Ford about 1996–2004** (SCP), e.g. 2003 F-250: best effort. Ford's details for that era aren't public, so the app tries two known request types.
  - **Ford 2005+ on CAN**: both the standard method and the older one some 2005–2010 Ford modules use. With an **OBDLink EX or MX+**, the app also scans Ford's second network (**MS-CAN**), where many Fords keep the airbag, body, cluster, climate and SYNC modules. Cheap clones can't reach MS-CAN.
  - **Not possible with this kind of adapter:** 1995 and older (OBD-I), some 1996–1998 GM ABS units on GM's separate data wire, and a few Ford modules that used a different wire (K-line).
  Everything above has been tested against simulated vehicles, not real ones yet. If a module that should have codes shows none, save the **Adapter Log** so the reader can be tuned.
- **Quick scan** checks the usual places for the make shown in the VIN. **Deep scan** checks every address (one to three minutes; longer on Fords with an OBDLink because it covers both networks).
- On older GM trucks, module codes show as **Current** (happening now) or **History** (happened before).
- **Manufacturer-specific codes** (like P1xxx, B1xxx) are shown with their category. Their exact meaning differs by make, so double-click them to look them up. You can add meanings yourself in a `custom_codes.csv` file next to the app, one per line: `P1234,My description`.
- Some cars only let a dealer tool clear airbag crash codes.

## Troubleshooting

- **No ports in the list**: click ↻. For USB adapters on Windows you may need the adapter's driver (often FTDI or CH340). For Bluetooth, pair the adapter first.
- **"The adapter is working, but the car didn't answer"**: the ignition is off or the adapter isn't fully seated.
- The **Adapter Log** tab shows the raw conversation with the adapter. It's useful if something odd happens.

## Optional: make a double-click program

```
pip install pyinstaller
pyinstaller --onefile --windowed car_code_reader.py
```
The program appears in the `dist` folder.
