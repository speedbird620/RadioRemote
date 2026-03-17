# RadioRemote
As an instructor in the back seat I have often experienced the radio either too high or too low. Asking the student to adjust the volume takes time from teaching. If it´s a civilian passenger you 1; need to explain which instrument in the panel is the radio, 2; remember what typ of radio it is, 3; explain to the individual which button to use, 4; tell them which way to turn the knob.

Since almost all modern radios today is equipped with a serialport, a fairly simple DIY-remote control can be built. This is such a project.

The project is open source and please feel free to build on yourself or get inspired. Currently the only the software is working for KTR2. Please let me know if you want to help and develop adaptations for other radios.

Please note that adaptations can be made for transponders as well. 

## Normal option

_Radio remote normal option, front side_

<img width="309" height="534" alt="image" src="https://github.com/user-attachments/assets/69de3e94-d169-4190-bff8-ce7cb5ebb48a" />

_Radio remote normal option, rear side_

<img width="440" height="621" alt="image" src="https://github.com/user-attachments/assets/9ce83a6f-9c16-4568-8fbc-d29d17585469" />

_Connector in the front seat with power, TX, RX and PTT from the radio_

<img width="504" height="638" alt="image" src="https://github.com/user-attachments/assets/d6b92631-d566-48fb-be2e-9f7456ea4d5f" />

## Minimal option

In case the rear instrument panel does not have a spare 57 mm slot, the minimal option can be selected. Then only the volume can be adjusted, but many times thats all you need. 

_Radio remote minimal option_

<img width="438" height="505" alt="image" src="https://github.com/user-attachments/assets/d71cc0c3-156a-4179-9cc3-36d0055cd815" />

## Design

The unit is a bespoke PCS with a Raspberry PI PICO, RS232-serial port, some buttons and an OLED screen. The main components is as below. The front and rear case is 3D-printed.

<img width="995" height="428" alt="image" src="https://github.com/user-attachments/assets/6b3f016f-6b58-4fe5-8e6c-93355d487aa9" />


