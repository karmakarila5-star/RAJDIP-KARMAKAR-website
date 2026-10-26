"""
LOOB APP - a desktop window version of Loob, with buttons instead of
typed slash commands.

Setup (do this once):
  1. Install Ollama from https://ollama.com and run:  ollama pull llama3.2
  2. pip install pillow
  3. Optional but recommended:
       pip install ddgs       (lets Loob search the internet for fresh facts)
       pip install keyring    (stores your Claude key securely, if you use /Claude mode)

Run:
  python loob_app.py
"""

import base64
import io
import json
import os
import platform
import random
import re
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

try:
    from PIL import Image, ImageTk

    PIL_OK = True
except ImportError:
    PIL_OK = False

# ----------------------------------------------------------------------
# Backend - all the "thinking" logic, with no window-drawing code in it.
# Kept separate so it can be tested and reused on its own.
# ----------------------------------------------------------------------
NAME = "Loob"
CREATOR_NAME = "Rajdip Karmakar"
CREATOR_IMAGE_BASE64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAH0AOEDASIAAhEBAxEB/8QAHAAAAgIDAQEAAAAAAAAAAAAABAUDBgACBwEI/8QARhAAAQMDAwIEAgYGBwcEAwAAAQACAwQRIQUSMQZBEyJRYXGBBxQykaGxFSMlQsHRNVJTYnJz8BYkM2OCkrI2g+HxQ0ST/8QAGgEAAgMBAQAAAAAAAAAAAAAAAgMAAQQFBv/EACYRAAICAQQCAwEBAAMAAAAAAAABAhEDBBIhMTJBEyJRBWEUgZH/2gAMAwEAAhEDEQA/AL+NQZ302jP/AEn+a9NfFe50ymPwLh/FZ4XsvPCHor5DSTM+v04H9FxW9pXD+K1dW0wjc8UAj2i7v1rivPBBcAgeoWinp2Njvd5z7q4q3RUqirEGq1UlXUPfJx+60G4ASaVtgUynFjhBzjBWlKjG3YsliFrlCStFkylb5CEuqByhZEBSEoaVoI+fCKe0kqMsNuEDDQvc3GeVBILZITCRuDhCSNxcIA6AnDNwtCd1859kUQO4wUNIA03HHsqZaRE4EG/K8sHNvwVIS0HsQVqR+sBabn0QBpEBaSSPReeFg44RbGF7nFov7eqIEbbbgLpbkOjjbFkDbmSO9twtZEhjGsMhBLhZzQPUcryoYGVbXs+y8Wt7ouCmcZQBfbI0kfxRXwLlGnRpDN4gcGtA3HcHBbavRwiVnk872b7jF1lLTPgliLmu2k2IsmtbSGopGAOBezDSebeiiYG0rLGRuu0izh2RjBID4YIErdpH94KKSmeXG4Ae02N+60pZA2dnib7Alo9QrBaG+qVG2Noc1pD22ew/6/1dLNEqPCqHwHIedzSfwTWsjjncXOduLANwtYkcJLHGWV7Ywbvjf5Ta25vIVlH1Lp9b9f8Ao5bIbbgxjHAdi14H8FT6XGvUpBz4zfzRn0e18lV9HFZFUX8WGYNv6tLgQgaT+nKX/Ob+azZPJHRwv6HXLLFlgsTRBajptEeaSn//AJhanS6A80cH/YEYsTRIo1DT9Pp6SSUUcF2gn7NlxjqGX61XTOtYA2AHAsutdb6gKXTXQtLxLIPLbhchqm3JJ5TsK7bE5nwkKZWXF/RBTs8qbObyl8wwU4SLJm2CXys7plPhBSDJsgkHFAD2LV0VxhGmG5FwtxAS3ASpSo048bYnfDcFBllj7qxPp7AYshp6IPHHzCS8iNK07fRXpogQS3CCkjcexVldpuME/cvW0JNgGfMhA8qDWlb7KoKOZ1/KbIiHTnts48q0ij2gDF1gpSOyVLKx0NLFdladTSMcXMFx6cKdkTyNwba/qFY20V/3StxpjnNtaw9Et5LNCwJFOrWkts9uL3+CkoagE+FML7Dg/LkfJXD/AGadOB5uVtT9FO8QOcdzfQYKbDIjNmwXyiv0j/rBMDXF7XHvbn29F6Wupi4lwftOQF0OXpWmNM3wo2seRe4FiCkGqaRLTxSGQNItk3yUy7Mjg0UepcHziQ+S/wBmx4Kjr4nTQmVkR233FzRbPB/JMpY2EFpaSDyByD6onTqsvoKqkqGMsWnabWN7c/FGhEgelpTJp8bms3OeDY+pH80m1CmfFWh53cXBtnjF1c+k2Ceh+qShjJG7rF/cWxb3wUP1jRtoqOjfJYy7nxTMbztBBafxV0BZa+gNYilpqiGKQN+tQgvacDe1wOPflNKT+nae/wDbN/Nc26OqPCr4jC8Bsczcn94O5/17rpcDR+nKUtNwZm/LKz5PI36d/U6zf2WLZYmCiyDWdPPFS3/tP8lIzU6N5AbO0k8YKGl0Gicd0LXQv9WO/gcL10bqSnf9YbG5oBtNG21viP5J3AjkrvXGoU12tjjbLM1uHE3A+S5vU+ZxNgL9grBrbnOqX3JJPclIpm5K0wVIy5JXIXSizCUumb801qGi1kG2AyusOO6Jkim3SFMkTnnAytW0ZOSn5p2sbYIeba30WeU/w348KXYr+rAHhZ4YGLIh7wD2Cic8Dus02zZBJdET47qMxZ4RINx7LXCRI1RIhCLZAWCnFyQpi6wXm+xulNjUDugueMLGQA8BEbs3Fls0i4PqhbLSNoIBcYRYhAIIGFpCQ1ENPG7vwhLCaRoAt2TekaNlrXSqmNrEjCawOsOfuRx4M+QYRMbbzC4KV9Q6QypgdsxbsO/wTWAh4GcqcMJuHZHqtMWYpo4Tq1JJp2oxSvAMYd5gRyL5Vbqa131gBnBde4/Jd06w6bbqNFL4DB420lpHN1wnWtPqaWeVkkTmPYCHAj07j2TkZJrkYy6n4VV4sRLRGWubYW47H/XdMaqZ+t6dUVU7neLE4XA9CbWHysqe+YlvO7da9k9oKx7KaoDHCzng49//AKRC6CukvLOy9gTIx975FnWXTKN19bp8W/WtP4rldBM+lkY9vBswH1zc2XU6L+mKcnnxW/ms8+zZp3wzsCxZb/VliOmBZdFDWAmlls8M8p8x7e6kZI14uxwNufZRV8giop3uAcGsJIPfCcJOS6gLSO597pRPYJ1qIJe42tc3skswLnWWuPRjkvsCCMyv9kQImxtwERHEGNCGq5gxpA5S5u+DZiioKwCunbGCL5SCqqTcoyte6RxJ4SyaJzuEKSClOT6BJ6l/YoX6zL2ciJYHjJF0LIwg8FC6LjuRPHqL24KKjrY3DnJSZ7Tm3Kj3ODhzZJnGLNOPLNFkEwPe61fJdyU08rsAozfcLHKNM6UHaCRNYqTxe4KB3ZW3iYQUGMG1JaQe3xRQqmkXJFx2Venqtgyk1Vq0oNo8W7lWoWDOSidEjrow21wD2yj4q9m1rS4A35XG5dZqzfZK4Lxuuaif/wBkj5XTFiZlnmid4o6sXGe6eUsgcDx8F8+6b1NWwO2SyFwOLlXnRep53GIuILuBnn4pig0ZpTTOoPjBZxcKgdf9MOrGiqonBkguSPU2Vu0PWI9RjAILX2y0i3zTKogDo3DPqEyLoRJWj5a1jSKiiJc+INaX7LAfZcBe3wtkLXT2udJE3lxfwe66X9IFCInyiRp2uF7j8Puyud00X1TWqZz27ot7bi9wQeExiOuGOK3RpmV1LC1oaZqnylvABPHyC6LQG+r09sjxWfmkUrmyzQuZlzHAMJFj5hk/Ip3Qbv0xB3PjNv8AelZVTRq0/TOyW9/wWLVYjBLfNCH+Zp2Sjhw/j6haRziSCQytAdHcSNOQCP4d0Qhp2FkrpWEDcwtdfi4yCfxRiTl+sSmaolkdy5xKTxs3SXPCaas8unkLiS4uJJKCgHkJ9VpuoiIq5g9U/YLDlK5mOcPNdM6hoLiSgJ3AFKbNajYvfCMkoSWNreEdK6/CDlHqUEmPjFAEoBBQNRGMplIAO6DlIN0tsZtQqkG0qGwKKnsSUE824VNkiiaPCm3EYQzH/epQcLPM2Q6N92V49+Fpnmy1kvtyljbIKl1wfVKJ47o6oft7oJ8l8I48CZ8gT4MqF0L7eQZR4G4qeKLNrI91CniTEraecuTvS6iSG4ke4WsQeDcHGfvTSio43uaHNGVZKLpyirGWkaWut9oeqKM7FTwJchPSuumRzYnN/WyPsLDvbj55XStJ1NldStcDd4sHD5XXK5unajTgJYvM1p3MkbkWHqmuiavJHWU5aTtl/VyN7bhwUTZn2O+Bx9IlIJaA1EYBdEdxv6cFcVc9kc7S4gxxuuWHmx9F9A6i1tbpzrZa9hx8l87VrZY66pp3MPiRSOs0fHP5K8cr4FZY1yXWilDHUsty9wDWTX7G+D8w4K1UR/bEH+a0fiqXpr2uo4YLOvI67Xd7f/d1cdO82rwc3MzfzVZe0M03TOw/NYvbLEdFFqOoUw5kI+LT/JC1up0gaAJI5DYnaT+aaJLX0wqtYe0/aZS7m/EuP8kYk5vrMpfM9x5JUA8sTR7KTVWOFWWvwSchRzmwT5dIVi5bYDUyWBSmaQkkBH1Zulc0gjuSENGm6NTcg9vcoSUc8lRz6lb93hAS1kkhswZKFxsOOWKCJPeyCqbAXFkvqa2VpIuLhL5dRkDeQh+Nkeoj0E1EhBPKF8TcUPJUPI3EcrynlbI63e6CUaG452w6I3cUZGwuIQ8TM+6Z0MDnyAALNNnRxxJ6SkMg4UtXpbxCXEdrq06RpO8A2TWs00/Vi22LJUeSsk0nRw+uu2ZzT2KEJtlPOqqB9FqDr3s7IPoqxJKSTc2TooU5B0bx6o6lmj3C7gkkUwv6plRPjc4B+3PqqlEOEky36WKeYDgu7WVw0+lZG0OY4gixGeVW+ndCptQjJbgixvG+yslZptVpkDXUkrqiPb5oZPtf9J7/AAUimlYvLJN0Ez1YF2OO32VYmpWR1JlgsPOHFo4uO6yp1IStLmk7mfaacEeuFBRVbJ5TnkZQSlYKhReNDn8Wi8M/uri/WjXUHXdSGjyyOBcObgjK6/0+DGCw3sRdcy+lKIRdcRSAZMbHj3RYH9jNqI1EyC8s9LIwWObj45/n96t+hlztRpHOBBMjbj3ulOm0IrKNtRSM/wCE1vim+Qezh87JxooI1SmHpK380/Ly0Dp1UTs3yWKS3x+5YiALcgGW/TFU4nDYGD4ZeUeg6cD9J1h58kY/8kYk5hq7b6vKSD9ouyLfgl9QcJzrpMms1r3WvvIx8UlqM3TGyscRbUDlK6locLFN5oy4JbU0xN7EhVvQ/wCNsSVFLHbBO5AO3wG7bEe6bVNNKL2KVVENQL+S6m5AvE16EuoRF8jnxtNnctSx1PITYiydzsqMgRFC/VKmRx8u34KOZSw2+gF4GGnAAtbup6Klb4gdtPsj4NL2G8mSjGxBtgAs+TKukdDT6Zr7SIoY7lOdLjs8IONgFsZTCkNjcrJNnThHgu2jkhrbHKsIjEkdiFWdBJe0EK2U9iziyHEzFqFTOefSB06ayke6Fv6wAkFcGngmZI5kwcNpIPsV9cVkLZoXC2Vw76RumZIquSroWE3y9jRz7rVFpGZpyRzarj8Kl8aN3e2ChmVjmhpEjroiUBwcx3lvyPVCOoXX8jx8CmpozyUk+CxaPr9VRyN8Cd8cl+BgLoOn9a1L42s1CPfF/XaLhc00bTpHHaCwufi5F7D2Ct9L0+KWg3UdcDUkeZj3Wa8dwB25KFqLGKc655HmoVOn6i90lPM1tTbIv9r4+/ukunSPj1DYTi6sWk9OtrWxy1Wluhka0Ava4knte9/4FMp+lHbmStHnaRm1iR7pbxjYZUONCf4jbu5AVF+lyEf7S6bISQ2Sn2kj1Diug6XRvp4xuB+YVX+kqlZUanpAJAIjfYnj/Xf5IMKqYGo5iMOltMdT9N1dWHudE8tYHE978W+Az8lDpX9Mwf5rfzVvbRmj+juIFnhl8jHGO/2ecfx+ap+kZ1qn/wA1v5ps/IDD4na9vxWKRYmCrLOgqW5ra88Hc1oP/QD/ABRqB092+o1B3pPt+5jUYk51qULoJp2PN3CQtJHeyTy8qydVAM1GoAxd5P3qsyHlRsbjRBIEK9tzwiZChXvCVJmyCIHxAnKHlpgQinSBal9wkts0RiLX0bSchQyU7GDgJlI7BS2rkuPRA5MdGIunwShXOAKmlu9+xvJU7IoomeblC2OSBYCXPzwjmuDSLdktqp2MN2ELSKq3WyhasZFpcHQelagb7Gx9lfYfCcwWIGFxzQq/wagHcVbXa54DQRJ5T7q8bUTHqcblK0Wyf9VIQe4uFXtWpmSl25oIKMo9Xg1CJrTI3f2N0BrkklDIzxcwyGzXDi/ojckZ445KVFC1/oeir3ukiaYZTklvBPwVPquiK+mdaCUOb/fF/wAQurCuaXfA2RkDY5hZwFz+KiytByw+2cm07pbVmPxNAwHm1yfyVx0HQqijeDNK2YDgbLBW0ULR9gIqmprchT5GwHBUaUT3xMDWxtb800h8wyFPTUjS0XCJdShgFkxOXszyS9As0TfDvZUnq+n8bW9BYz7bpHs57fzV6lbtablU3qhxj1zQ5GN3Fkrn2va4Frq4v7IGS+rLv1nEyHpSIMbsAewAD2BXMtHP7ap7f2rfzXUev3D/AGaBabgyMI+4rluif03Tg/2gRT8kXh8Wdyv/AKusW+32KxNoz2WJK6GZsNNqU/7rZ5XfcAP4JoVXLE9L6i6990k7r/8AuFELKXrc7ny7nklzgHEnuSkkj+Uw1l/mYfVjfySaR9lRpxrg8meg5H5W0z8ISR49UpmyCNnyKPxbBQvfjlDSS2S2jREJlm9EDO/GV4+Q+qGlfdLoaiGKW1S8n0SrqPUZYYD4PJ7+inqHuifvAuO6CqHw1DC19iCriubKk3VIpk2qVhcT9Yf8E60PUKqW7ahva7X25Rn6HpAd+zPKx7fAf5B5U2c4tUkZMWLJjlulIaU1YWyNtykvUXWUxmNNSgFkZsXnufZeSTuLtrGm5QdVojKpod9h/qEuKinchuVzkqiH9P8AV9THOze22eQV2hmos1roytM4/WRR72n0IyCuEabpH1eUb3XAP3rruhEwdKTNtmXyi/olzS3fUbz8a392JaWqdfJPxT6grDcAmxVcfGY33GAiqeU4JSOTS4povlBVNkABwU2pjHdpJyTZUmhqCLHdcJ9Q1Zc4biDlNhIxZcVdFvjFmrJHXuhaWoDmjPKncQVpvg57VMhmALDdc/6+lfDVaa+M2cC4c8gkAj7lfpXAArnX0iODtW0qMkZDjbv9ofySnKuTRp4b5pM6F1k/d0dTOPJMX/gVzXQc65Tj/mBdG6x/9H0wOLGL/wACucdPn9uU/wDmBOfaEY/F/wDZ3rPqsWWWLRRksfu/JIaNnjdHyi1y+KV33lxTuaQCFxBv5SR9yqNZqzdK6Qo425qJ4PL7A8n8VAVyyl65iOA/3AkEsid6xJ4lHAe+1VuV2ChNmLojklvdDSSZXkrrlDSPS5GuJtLILIV8gJXkr0OSSgY6KJXOUTnYytXOtdQOk90tjUZJY88IKWGIP3BgupJJHbufKoXEk4URbNHEuNhwvHUrnMJKP06ifUPs2yffoiTwbFv3KmwWVOnow51rZTqg6fkqxbfsHqjGaXLEQdhPrhWTSoHRsaXAjHBCFO2DKW1cCyl+jotkbI/UdzL32iP+Kss2ktho2xNu4Nxco+mmsACVLPLduSjpGX5JN8lDrqTbcWN28pbbZx62Vs1CJriSMEpFUU3nyDnKQ0bseS0R0s1jbgp7S1AJBtYHsOyq/mhmyjoKgjjgKlwXNWXejrNpFjYeqbR1IcOVSKOsIt78pzTVQt9pGp+jHkxjqaa/HdUjqOF1f1vp9O1tzHC373OP/wAKzeKXEKPo/T3V/VddqkjB4MLwxrj3LRYW+4lWo73RMc1iub9IfdfgM6cDBw2Vg+5rlzPQD+26a39qF0n6QT+wD/nN/Jy5p0//AE3Tj/mLVPyRjxP6M79j+ssWWb6fisTzGZJq0TqWWMU9WxzmkNvTPtx8FTeq7P07TCzxP1UDYXh7C3a4D3XSKjxT/wABzg5pyD3QlfTxalFJSVzC6NzQeLEH1B9VfYMXsdnHqx16KIeyRTq59XaOdG2QCTxWWLmuIsbE91S50ts6GLlWBS8GyFeMIl/KHlOPZLZriByutdDumACmmGClVU4sKAY3QRJMLc8oaSUX5Surr3MNgLlLZK2ZzsMcr2Ni3nS4LCJmg3cfKoJa9oNo7fFA09PPVNG9+xqNZo0NgTI8n4qqSNEd0laRrHXPYdzXkH2KPpOoqqBw2zOI9CUE/RWkfq5Hj5rRnT9c83iII9whaTGJzXos9N1nLG4B1iPcXTyg64pS9oqI2bHc2HCplH0XqFSR/vEbL9rXTIfRf1BNG+SinpZgL+RzthKijfQnI4ryR0QV9PLA2eme10buLdloNRY7F1yL69qvTFU6g1WCSnJP2XZB92nupWdTPLiA/wDHlC00J2R9M6hLKyV2CMcL36t4jQ6wyqNQ67vcN7uTY5V20etbPCASMiyH2E04qxNq9BYkjBCUxOcx1nXBVp1M2a4ct7JBPT73EtBwhlEZCdrkmpZiM3PsU3pZjtzlIoYnBwBBtym0DCAChaJIdU0jnny5ICv+jUbaDS4IWixtud7uOSqJprPCaxxvlwC6DDN4lNE6/IWvTo5uqfor30gOH6AP+c38nLmvTx/btPb+0XR+vSDoB/zm/wDi5c46dxrNP/mI5+aBw+DPoPb7rFJ8li0mGxwBkm68cL4xlJWdV6I5oP6QiafR1wpmdRaO/wCzqNMf+tAHQg+k2k36ZFUNH2DtP8P4rj1QbEhdz6kq9O1HRKmGOtpnv27mASAkkei4LWvtO4Di6XNmzTdUDyHKgkNwsfJcn0Q73pTZvijSU2SqtzdMJH4OUvnNyhsZVi8UofckXUsVK0dgiYwAt8KnJhRxpEHhhowAonzOj7cKaQnOENLnkIbHHrdT2G/5omLXnMFg4felEsYINgoPAwSQrK3tFvoeq/BcC4XV46Z63pMNlcWuK4zHCLgEWT3RIwJW4v7qlJx5QM1GaqSOs9SUOl9U0D46loeDlrwPM0+oK4N1X0nX6DVO8OUyU9/K+35rtmjytbEBx6ojVNPg1OnMczQWo1lZhcEuD560+tmY9rX3x3XR+kNQ32aSShNe6MbSlz4L7eVL0vRvo6ja4XBPCGbT5Gx8aL3NF4jW4JB5Poh2U1ibplT2fCML10e0kJbZS4FhpQDuRUEHBIwMKcNvgqdjQ0hCRsmpp46eeFpaXvN9jByTwrlSteynjbLh9iXD0J7JX05RQtj+uOjBqH3DXnJa30Homzj5it+GFK2c3PkUntRXOu3fsEg/2zf/ABcue9On9swf5iv/AF2f2D/77f8Axcuf9OH9s0/+Yhn5oZh8GfRN/gsXmPT81i1UYThrquQG+4H/AKQojXSXz4ZA7FgKBdVxHIeCoXVEefOFgcmdlY4v0Hy6g/cCGxXBuPIMIDU3Dxy5v2XeYfAqF07D+8D815O8S0/2tzo8fJVGTboJ41HlAUknuh3S8rWaTlCPksiYyJPI+/dDONytHSLXfnlAxqJd1l4ZPZRly1vglCw0iUnco3tBXrSpYwO5VDEiCOlMrhbFkdBozpRi91JA5rXJ9p9TCMHHe6qypKkJP9npQA5rd2OERQ6ZJBK0luLq8ULopwHNAW9RTNsbDHNirZneSuADTrR4cLDsm8czQLApdYDHBCxjto5VCXyEV5bNC5pAVZfGKeobYcJzJLi5OEpqzukuM2KjZceB7R1H6vF7IkSh/KR0s+1lh6d0RHUWN7/JCRoZ7wOFqXlz2xM8z3myB8fc7lT6TMHam1vJAJPsrirYM3ti2dE0xojpmMHDQAFKSPEdb0QtC+8YW7XfrH/cunHo48uyv9eO/YQAzeobf28r1QOnP6Xgt/aK9ddknR2WNh4wv/2uVD6eNtWhP/MWefmjZh8D6O2f6usUHjD1WLTZi2nzA/UojzSQj4Ej+KjdWwuZJIKRu1hANpHd1C+MFbBjG6VVD96SWMDHYB9/zCR8h0fg/wBIZNSpA7NI8D2mKN06annaHwB0W57YneLLZrdxtck9u90lkiBsjjExmizgY3Stx62Cimn6JLC49N/+k2pxOp6qWF5YXMcWlzHBzT7gjBHulsj/AFW+nxyzUs4AuynAde/AJ4Q8jufRKZog/Ro99uSvGy+6ikuUM5xahHJjMPuOV7dBQzX7ohrroHwOi7Jbrdj/AHUAdytS6xvdCMQY2XN0TFVBrrXSjxCO688Szie6qgrL/omoBlhcW9FZDVNey4PIXMdKqyyQF3CtlHXs2gD0VdCMsU+Rw9wLlqHEPIuChPHDhzn0WwlANyVZnaPKhwAJ7JZLMLmxHNiFvqFUGsNj96TGcvecqykNGz5sERDuJ5yllM7c7JKZQOIAVFk8kgijc8nACzpSQyai57zkkpJVVwqKwwxnyRg3t3cmnSp21I+KbjVMVm8WjqlC60akY67nfFCUbv1d1NGbXPqVrTOW0IuuXX0mMeso/IqjaAbapD/jV064N9Li/wAz+BVL0C36Si/xpM/I14vA7X+k/dYqz4vusTzOULrTSaShqH/UW+G+Lb9YhDi5rd+7a5pObHacG9jb1VWdMRTOh7F4f9wI/im5raSqqqyp1iueyXUYmCKGCIyyFzJDgNBFhbuSt9Y6bqaKkpqttHWSQzuEbQ6Pa8OOQC25yfYnI7JEo88GvDqFtqXZWSfMEZKQdLuOTLn7lbdM+jzUK2K8gZTT2v4E0tnD2JAIafYlbu6FkNqer1CmpGhxvsDpyTb2AH4qlFoueeEqS/SkUbzHpGogG290Q98bilDptxO77X5q5dZ6DH03pkEceoRVrap5kBYxzCA0WyD8VQpnXvZXXAamnJtBQeCFG8AhA/WHMNnceqnbMHBA0PUkz0gt4UkVQBh2Fpe6jewFC+RidBZm9Cs8S/KAJc3heiY90NB7g0uwvNyFEt+69EgUovcMKaXa8FOYNQEbD6BVhswHdbNmuRkoaBlIuVPqAIB3Io6g0g7SeFU6MSyEbCdqfUdIDmQ59FaQmVmVEj5XYuAtWxlpGbpkyJmLDIXjo2B2QowSOAEWxz3Vn0PTXSNFRUC0Y+yP6x/khOntNbWVIdKP1DckevsrjMA2EhoAAGAEcIe2Knk9I4zpRvPKfY/mrT00bTjHdVPSDeWUnBt2+KtXTR/XN+KOPYzP7Om0DrxhFN7pfpzrsRwKcmctorvW9v0ZDz/xP4FU3p/+k4v8auPW4/Z0JziQ/kqZoB/aUX+NLl5GnF4F/uFi0usTTOck6kibpXVmnyvLBK6DcRHgXvb5LtnR+pwVdHHHK9rwSCAckEcOB7EL50+kKse7q0yXO1kbA30tZdK+jrXZWmKEOYIza24jKCXCTBirtHQJ26oaiqM9JTxU8bwGPbUuMjs5NuACPgUpr9XigcA6TxCedjhf2+KN1/VfCrJYnOa0ywB4O7uObY9AO65hrta7xnEP3juTYi6WxkV+inr3W3ahVNDiSYnOjO7kgE7T91vxVR8W4yVmpSvdUysc6+15LT7HNkGH2KZ6HwCJGhwQ+58TrjI9FIyS/K2IDghHo9iqge/yU7ZAe6XS045bg+yibNLCfMNwQtfg2M67HNwV4QCUuirmONi7afdFMna7ghLaY1ST6JTGOyzwzZY2QEcrYO91QRq2PKLp42NI3ZKgDhflbNf7oWyqHlJMxpsOPZWzQdLlrNpeSyM+oVb6ZoBMfrEw8jTYA910DTalse1osAlTk10aIafctzHlB0xQ7AHguPe5Wld0TC+z6aV7bZLTm6babUBzWm6dtkAaD6o8fPLMOaLi6KZpcIgMjAzYGeUDuiao/qX2/qn8kfqcUccpe3Dn5ISqsP8Au8v+E/ktSdmOqZx/RzmQ+ytPTZ/WBVXR+JD/AHQrP02fOPihXZqznRtNd5ExacOSjTXeQJswjYSnLo5suyudbO/3CBtjl5N8en/yqfoP9JRf41butWMdSQSFoL2uLQe9iM/kFUNBP7Tj/wAaXLyH4/AvSxeWWJtCD586tHi6kya+HxN+VsJv0lXugZC6wNsZSfWz4hjd3GFtoT9rCByHIJcxKh5HSutqiWmbpOoxhzobFtw64I5t+apU9c6Rx3EYwP4K2adqEeo6NNpdaT4cjbMIOWP7H71QXlzXua77QNj8UCY2qAq5+6q3f1m/kh3C6Lq4yWh1jgocjCIfBEYUjSVra5ytrGyqxqRsCCMrV8YctgF7tNvdVYaQFNTtPZCvp3NyxxHwTYsPoo3R3U3EcBXvqGfZkcfivRV1Q4ePuRzob9lJBQyTODY43OJ9ApaBcZLpi8VlWT9sfcjtMpNQ1KrZBC+Qlxzt7D+CsWl9Jl7g+rfsb2Y3kq66dRQUFPsp4mxj27/FRtJBYoSnJJs1poW0FLFTMN9gsT6lTw1Ja4ZQ07ruOVE13mWOXJ6THBJUXfRq4naLq3085fC0Lm2jSEvaAr3pr7xhXj4OXrsaXJ5qb7zW9ErrH2p5T/cP5JqJWPllje1t91w4tBPwyldW6OJ5p9VaylinPhxVsFzFuOA17HG7D6G9itaa6OK3ycf0c+V59grN06bPHxVkh+i40kLnRau2QlvLqezfwcSPuSql0PUtMqfDqqV4GS17BvY4eocMFRJ2NyZYTvay36a7ypuw+RI9Nd5QnMR8qYjFLsQ9ZH9nx/4/4KnaH/SUf+NW/rFwFBEO5f8AwVP0Qj9Ixn++gfkPx+Jer+6xa/JYjEUcC1iMsdb1QuiutVuYThyd9SRAPbYJHQjbXNKr0VHuy4QxOYwPjPmCrtcT9fqQ7kyEkfirzplP4tMx23HqFUNXpnjWqywuPFIS0g91ugEjczPCHDLXB7Jk2mk4DDde/UZdpfsNgMqmzThauhU+PHC0sQLHITU0jzwwn5KI0cl8MKDebPjAmsvkG/svQbGxRrKGVxw0hFQ6XK4gOCm4JQFrADyERDQyzu8jDn2VhotDZYGTym/cKxafp7YLFm35qtwVUVSg6dD8zfdeysVJpsdOwCOMAetk/jpd1rtafayJio2k22fcopC5CaOjcDcXPxWlQPD8issdIwDuPiqzqTgayQA3ANlJStGjRxTmAy8lRA5UshWkYu8JLOxEc6ICJA4q9afII2Au4VS0dgI44VkhY9zQ1mVcTma2W50S/wD5XuHc4U0kcdVTSU9SxskMjSx7HDDgey08NzHAO5UsOLpzZxWuQfpOrmp31Wk1UhfLRkeG8nMkJHlcffkH3CczOfT75oZTHGcvF8D+98PX71Wq5xo+qdIqgbMqGvpJPfG5t/mD96tIdYWtdvomwlaMuaO2V/oHHpdPNJJJT1LGuJuYwNwH3Kaoo20dMZqqphiYOL3yfQDkn2C0ZHHv3va0SsO0vAs63bIzwpS2njlNSYg+o22EjiXED0F+Pkiuhe5iDU6cajGwTU9THTtJcJHEMJx2abm3xt8EqpOnaWOrY+mq5G2dfbK0H8R/JO9UmlliLyeOQlM0xY8G/lGUL/QlkkuEPP0VL/bQf9x/ksS79JH+zd/3BYr3E3M5P1hTtjbGTzlVehberZ8VaeuZN1b4YOGhItHgLqxuAc2UsKC4Op9N0jXUMeAVVdWijj6srIJmENkfj291fNDjEdMzZ2CpP0jNdS9SU9Qw23ta6yv0Kv7DKLRQ1rg4edmT7j1TKl0mPZfaL+4W2jVzdQooZGbfrAwG9yPRMC4NLdpO0mwPofRSkXuaFj9Ci+1EwBl7W9D6KJ2gMtcNTxszozvFiO7fVMYyyZm6PI9O4WXJj28o6Wn1Tktr7KgNDYyxIFgpBQxsGGBWiSAHthDvpBy3hLs1b7EApRfIRMNLYA8App9Vt2IUjICDwpZHIGgityEU2IA8fCynjhAGVKI84VgNnjGkRHF8clc7qnXqZf8AEV0sN8ts5C5fXAx1s7DyHn81bZs0HkyCRxubrancN4Ub1tTjzIGzrei16IfThXDTdoFuSqTpB2gZVooZsixRRfJyNWrbG9RGOO6hY2yx04DNzitadxcHPPBOEZzGgHXYfFk0toHmFZG/5C5Kdl3r2SwvEuoh7gfDgBDfd5GT8hj5lFGQAHKdjVIyZ3bSJvEF5b2Axn5BRVcwsQyxKglJMJANjIRcH35/BaO/vHP5ozO2RyWkgIOCq3qMn1eQAnk9+FYpneTGEi1WHx4ztORkYVMkewD6y7+yH/csQH1aX+oPuWIaY20UnqGUzajM4numXS2nF8rHlvJwbJSyN9XVgcgldE0ajNNEzGMGytclye1D7TrNAAx2sqp9K9E+SGkqmAkNGw29Faqe4tbv2W/UNC2v0aaJ4uQ24RiE6lZx7Q9ZnoKmNwd5ARcLqtNVwV1EJmkOa6xkt+a4xVxOpapzS3LTbKt3ROsiCZkMltjvKQqsdKNoujneHIInEXI3A9nD2UX12WmkEjLg3t7Fe1YbTyRwVLr00maafuwYwff80vqZJILRVDRf90jgj2VgxLRpesUtdtjc4RTk22uOD8EzMftlczqD5SWkg/aB/kUz0nqqppWNZVN8eEYBJs4fNZ54vw2483H2LxsC28MFDabqtFqLA6CUbj+47BTAt9klxa7NCdmgjvlSNj5wsHIUrHWVlNmgj7lcx6tpzTa7MLWbJZ4+a6pfsqb9IdA6WkhrI23dCdr7D90qPo06PJtyU/ZR+VLA3KgY8EKRsm0oGduyxUAsy4KZxPcGl26wCR6ZUNwHFOH0rJiLSlrD2BVx5OfnVPkeU8zHwN3OH3qeKqG7ZH5z7JNT0NHHsHiPdbkXTuiMUR/VtACakc3JFegptNI5m44PogXPf4vhPBBBz7p5A4Pah9TpDPTyCPyyFpAcOU2LoxZMe4Ahf40rSMtbcA+p7lbVg2gHiyF0AktdHI0h0ZtlSV7y427cFM9GKSp0DBxkcRfhRzs239COLLWF/hvG8ot/mHmF1RBT4J/rfgsTDwSsULs5p0hphkldK8ENGQbK4vvFEAO5AsotNgZRUZawYIz7r2rcHujzaxBKiQUpWw2mcbNJPe2E5p3B8Ra7i1kopxeJu6w+CPpXEdxZEAzlnX2l/U698gb5XG4VZ06Z0U7SOQbrrH0iUbajRHS2G+M3+S5BG7bJ6IWaMbtHaNJ8LV9C8GoG4EZ/O491VKyvl06ok0/Uh40Tnl8ct7bjfGexAR3QFd5BGTe1kv8ApGhdSVkRJ3QPbctP4G/qr9C6qVA9f4kQM1M81FMckj7Tf8Q/io6GWOpgIB+ar8VZPTNBo53vaQLtJ8wsfxCbUtbSVT5ZJiYJcAyxNwT3Lm9/koOTDGiSCQFpcBfJHIVioOpq6kYA8iaNvAfzZIdswhY9wE7C3eJIrny+pHIWjZLu2XB/Aqmr7LUmujoWndX0NTYTMfA835yPvT+krKapa10MzHAi4yuP0w8NzrNuCeD2TjT5ZALMeRa32Twg+JBfM0dTNuRlQ1UDKmB8Mo3RvFnD1VJgr6loDmyuDgBcXwm1FrNS7yyhrrd1TxP0WtSlyc21mll0zVailNy1jvKfUdlFG5xtcWVs63iFSYq1jACBtfZVRrhws84uLpnotLnWbGpILp5S08prTVhNgXFId6kims7lAPklJFspqmzgb3KcUlUXO5VMpqvaU2pK2zuValRjyYi+UM5sDdNWuDmqn6fWXAzhWGjn3AC6fGVnMy46ZK6BrJ3StABIz7pFXutOQD3VlIBCQavTujf4jAdpOU1P0YM2O/shY4hzxc2sjYJN7LC1x6oJ4u6/cLKeUsl82GnCszjDPosXu+P1P3rFZCvzPIaWtxblBPc1zwcc/BSSSAfaIuMXt2QoI8UO43G2BhWRDmmJaAzkWwmcBaLB2PglNJd1vc8plgE/C6sFifrR37MkiJw4G+Vx50W2UgldW6scXwEA4AyFzWaMhwNkEuzRi6HvRc5i1OFm6zXGxV96x0kaxoMmwXmiG9hHcLnvTQcNRhIsAD9y67QmzAL3FrZ9FcQMrp2fN05fSz8lrmnKPgmgqGATOc1/Z4wrT9JnThoa11bTsJppjc2/dK54ZHRYtwiQadqy1Qmtga6WiqBKzaI7btpTqn1gkkalT7rztAc5mQPZwVHo69zDbcQDyOxVp0nV2kx7m3Y0+YHIKgRYKMUVXDG+nqC1xL2bT58gm3vwi6WkmAD43xytAxZ1nfioKIafV2P1dgeH7w5h2m/yRtNSwQsa2ConjAcS5r/MCoKkwljXgjxo3sPckGyOheLgm1xwQhIJK+EXYYZud2x+0m3GD7IpldUERk0ryAAHBzB3KsBhkjI6qlfDJtIc0hc4rYnUtVJC/wC0w2XQoq0uALIHGQN48Kxv/qyrnW1HNI0VwhcwNO1xNsjtgJOWG5WdH+ZqfjnsfTK34i3Y7GEu8YX5Ukc/a6yNHo1NDJrz2KOpqgtIyk7ZccqWOb3QlumXHTqy1huVkoK0YG5c3pqotIynun1uQS7CilRly4kzplPUCRosVNK1r2EGxBVV0/UA+wabBPqaZpjHmuU9Ss5eTFtYq1Gl8CRj2i7DgpfKNrXWNyArW5rJWFrhcFINVpHU9iwFzCnRlZgy4q5Qq8V39VyxSfNYiE0KhctyRlaBr2AN4afmtmt8wcAS1eh1pG2NgRjCIAZ0Di1rPEy0k2KLnm2i47GxCHpXDwnbgA4dkPVVLN20u7YUslCrX3CYNd/WBHCqNTT+cAAel1cHxmZjwb+TgpbU6f8ArLBt2kIHyNg6I+nqQsq2PLM49u66JHYR2GCPxVd02nMT4xY+Ui5KsMbrkjsiXAvI7MrqWDUaCSlqWB7Hi3w91w7rLpeo0eqcQwupyfK4Bdza8t4soq6mgrqZ0VSwOa4WyFd0Xjuz5jILHJlp87mvbtNj6q/ax9HE1TXPdRSxRwnOVBD9GdYwG9VF7WQ/JE1rFIzp2QyEC4BOfVW5lK6WPcbDCWaN0hW6c4E1DHAeis9NRyxtLXEHFrqfJH9AngnfQugpA0B7472wTdFirbGbC4I/FFihO21wLG4Wfo4EZcVXzRXsH/izZA+vNxsc0kj7lDXQGtheyY4cCOEzjoGC3luR3RbKMADHCB54jYaRrls4fXUs1PUyR+G47Ta4CEc90Z8zSLLvX6Mgc4ufExxPqFq/Q6OT7dNEf+lZt1vo7C1CS5OExVfa4RUc4PddcqeitInBvSMaT3bhK5vo60838J8rPTN1boOOqic+jnIsb4RsFYQcmyss30eSD/g1RHxCDd0NqMH2Hsf7oGhqzwfsK0mtc2xvdW/TqsOAubn0VOo9Ar6Y/r2OI9Gp/Qh9OLOjeLdyFE2hOVRl0W6nmLgLIp0TZoyHC4KR0VW3bkpxTT7gE6Ls584URfouH+r+KxH+KPRYitidv+HPHRBsRa4EHgXWn1dobhwt8eFO6ZtrOyEHO4PGy5/JabOcbzTeHdrXEDgXPdCxtdKSTa9rXW7mNk2XIx3UscZaxtrWB5B5QlkkbdvmaO3b0XgiEl3AC/Nitg4Hc25HsvYXbDnIyPirogTT2MouNrjyPVEvqI4iCSNyr9dqgvshPHJS51e5x8zilTy1wjo6fROS3TLj9eaLnBQc2p3cbGwVZNc61tyhdVEnlIlNs6ENLGPotI1A2+0pWagCPtZCp5rHeqjdWPJwUu2OWBMvUdWH/vIune1x5VCgrnstlPNOriSLnCFyKlp+LRbmMDm3UgixwgaKpDmg3wmsbmvYCEUeTJKLiRNaApWLHCy8YblFQBKGLYY5XjXdivdwV0Cza4XuFovQVZRttFloWhbBy9soQiLAvPDbwQCPgpSvFKLsHdR07/3QD6hexUjmn9W+491vJcHC8ic9rlES2S+DKsUm8rEYNnNA/BuTyMjsiN4LBvs/8whH5vtPm9B3U8ZaWNI7DK0nKNZHbWW22cCO/ZTxuuwCwI9VC82eARuBClpmjdubYN4IUKJ4NjiQ67SCluuVradvhRkXOSQmFVUso4Xv4xYFUqtndPO97jkm6XkltVI6Oh0/yS3S6RsZiSvBJlDbuy2DllZ3UqJi9amRR3XhVBEm+5W8Yuht1lvFLYqMtBjBcppRv22F0mY7cRY4TKmvbPKW0Wy00MhaxucFWGlk8rc4VS02W9geFY6V9m2ujgYsyG27cwqEYK1jddhsvSUwyVRI11l6HKIcqSyhTJQ7C9UYNl7uKgJJbC2BUO42WNeoQmJ9V4DdQlxJXoOVZCa116Gj0Wgflbg91ZRt8liy6xWQ5XFKfGO0Xsb2Pqj2H9WC3BJvb1CVUrmOBuDuKYRF3hgG9rLSclm5y8el7KeG4G7Bse6Fb5iBuI759VvPMKehkkd2GLdyoXFbmkhDrlf9YqHNYbRswPdKS66jMpke5zuXEkrdoWSTt2eqw41jioo9GV6vQMLCQhHHl1hNwtSVhKoho5eA5W9rrNqhDeF5Dk2pJdxDUoYLFH0Ys+6BhFjoxY4KeUkhIBCQ0bjZpTukNvgojLkQ3heRypz7cFCRncPgjIuAmJmOR6GkLYC2VIB6LUglWLbMBuvVpkLwEqyiTK8Xo4ytX3UKPQblbWNsrWPm63JsoQ8BypWmygDgttwAVkCN3wWKDeVillHI6UNLWva12MG/ZN6aZziTYEcWQgh2tvHwVJSktN9psCtRyWFHaZMA3GbLTW3W0uZoBGPVbNefHsTnsfZETBlVQSxhzCXNte6tq0FjltmmygtOVK0oaS8Mr2Pu1zTtIPss8UeqxtHrYtNWgvfZRuflDOqGjvwh5KsDgqqCtBj5FtES4pO+r7AptpwLow491GqKsMaB3Xtr9l6AtgEBaZ41lyjqZmeFBE3zBMKZmRZLbI2MKK+AnVM5KadvomUB4upYiY1gcRhHwuxZLIjchHRlHFmSaD2FeuHoomnKmHqmoQ0ROBWoU7hhQkXKhR6Dhe2BFyVqcLUBQhKBjC9dYrWN1sLY2VkPLeywMOV6LFbAqENLOWLdYpRRzdrBsIacgjHqtGbbXF7HnPC9ErDZRloEhLTghazkC3qGeWGnZHSutNM8Mae6ZnSY6bTGuifIJW+ckO5P+rpL1MyRpoKyNrntglu9oRtVrEdXRNjpHkPcchwtYJi6Kq3QHr+mOfQxV8Ju97dzm+o9fyVRMsz37WscT6AK+ahUufI1kDtsUbQwe9kt8FodcgXWLNON8HotHHJGFTKw2irJOfL8Vv8AoeYi75VZC1oWhIASN7NQgh0UNkDnvcQE5jaGAD0Xr3i+FoX3UtvsJEwKkblDNKIjvcKmGG0zM5TKBlkHStyMJnTsullNhUDcXRzGYFkPALYCNi4ViZMIgvcI6MoSNqJjNkaM8uQqM3AU7H5sh4SiGgXumIRI3cbhaWspXDiy9KOgQY4XnCkeFC8m6otGwd5hlSXueUPytmG5sqI0ENx8Fl1ruxZeXzlWUb3WLXCxUQ49qeqQ6a5jJi7cXXIHYeqaxEOY49wqNqLW1VBV1sz2vqC4bWg8C6t+nOa2mjzucWA/gt8o0cZOwkSFryNrXNPN+xQmqfVo9hbCwSfukdghNU1IwTxw0rC+rkw1o/jZKKipld/x7eIPKbcJORuMTbocW/Jb9DEz5XnjX5KUCcg8qVsvusTR6BIOdLfuoi8eqgMmFqXqUWTlywOuoC/3W8ZuQoQLibchH00V32KEpxdzQm1K3zi6FksKpobPsmVPH7YUdPECQQmVPFcIaFykaQx254RjWjstmxKRjLEK6FOVm8RxZTMUbQpWI0LZNC6xU+7GEM0WUzXYKYhbJ4337qRzrBCMNjdbukBsESAo3JuCoXL1xUbviqZEenC1L7C45XjjjlRk2NkIRKyS628QE5KgWreVLJQbvCxDbvdYpZKOOdQaJS/VHz0wcx7RawOE5oWEafAcXEYx8lK17JQTe98WK9kLWw2BsAbWC3OTfZw6EcDh/tJVyEguiYNvtfCU1Mu+d7h3JKdavpbnVEuoU8vhybBub/WA/ikBab5Sczs6/wDOiqcjwHKla7Chstm3Wc6xPuwtS5a3WhKlEJA+xRVOQLZyl90VC+/dU0Qbwv8AMCmdI+5uDwkcD8i6Y0km11+yUwqLXppDmc5TemAsqzps5D8cFWGGWzQriZ5oNGV5cKMvsFE6QXsjoUEB2fZTMeg2PClDwoimgsOW7XBBh9lsJEQNBm/C1BzdDtfjnK3BIapYNBN7i6jJJWgeQs3XVgnq0dyt+yjebFUQy1lqcFely8JVFm9x6rFHcLFCHGdOjr6eSMvqQ+H94FMq+uENO6WU7WsFyQhWSXuCBe6W9Ty3oI4QfNM8Cw9F0O2cMs8lSanSm1DLESMBI4tcKrrKnV7ad9UoST4Yu93pbstISXRNdzcApOZVydX+a+GjcrAvcLAMLOdczstXcLYla8qiETltFJtNivHqLgqyDSCVqa0crTyFWYpC11/VMqSexGUuURidl007a9mDY9k5p5A4hj1UtPqCyxDk5pp3eIHXwqjwKnEfvJYObhQPcL3upIJmys2kLQhvdMM/RqJbcKWKS/KGeG3wMLZrwOFRA0yi1l4JMoPcb8ra5vyoyqCzKQcKeOS4sUHE4Ai5Uhd6KgWg0PC1L/MhWPJW9/vV2A0Fb7d1q43yoS+zQsLtyso3Luy8BzZaBehwuqISXWLXd8FihDjTnujNgbgnuq/1JK8V8RBtZm4W7GyxYujHs4gWIWwdLP8ADuC9zdxvk5TOribFT02wWvGPyCxYlZ+jf/P8yBq9usWLIdw89FqDgLFihDx/ZRO5WLFZDQlSwvcDgrFiphRHFHK/a3Kf0cjwwZWLEoKQ6ppHXabowuJWLEaM0uzAb3BW1hjCxYrAMstu4WLFZRs3le3KxYhBPYybqa6xYrQDN25GV4ccLFigJ5c3XlyFixQhtdYsWKEP/9k="
CREATOR_PATTERN = re.compile(
    r"who (made|created|built|developed|designed) you|"
    r"your (creator|founder|maker|developer)|"
    r"who is your (creator|founder|maker)",
    re.IGNORECASE,
)

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

DATA_DIR = "loob_data"
CHAT_DIR = os.path.join(DATA_DIR, "chats")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

PERSONALITIES = {
    "friendly": (
        "You are Loob, a warm and friendly AI assistant with a casual, natural way of "
        "talking, like a close friend texting. When someone just greets you casually "
        "('hello', 'goodbye', 'bye', 'good morning'), reply the same casual way back in "
        "one short line - never define or explain the word, never lecture."
    ),
    "teacher": "You are Loob, a patient teacher. Explain step by step with easy examples.",
    "short": "You are Loob. Always answer in as few words as possible.",
    "funny": "You are Loob, a funny AI. Answer correctly but add light humor.",
    "coder": "You are Loob, an expert programmer. Give working code with short explanations.",
}

MODES = {
    "general (Ollama)": "llama3.1:8b",
    "code (Ollama)": "qwen2.5-coder:7b",
    "math (Ollama)": "deepseek-r1:8b",
    "basic (Ollama)": "llama3.2",
    "Claude (strongest, needs a key)": "claude-sonnet-5-5",
}


def setup_folders():
    for folder in (DATA_DIR, CHAT_DIR):
        os.makedirs(folder, exist_ok=True)
    if platform.system() != "Windows":
        try:
            os.chmod(DATA_DIR, 0o700)
        except Exception:
            pass


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_claude_key():
    try:
        import importlib

        keyring = importlib.import_module("keyring")
        return keyring.get_password("loob", "claude_api_key") or ""
    except ImportError:
        return ""


def set_claude_key(key):
    try:
        import importlib

        keyring = importlib.import_module("keyring")
        keyring.set_password("loob", "claude_api_key", key)
        return True
    except ImportError:
        return False


def open_file(path):
    path = os.path.abspath(path)
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def is_creator_question(text):
    return bool(CREATOR_PATTERN.search(text))


def creator_image_bytes():
    return base64.b64decode(CREATOR_IMAGE_BASE64)


class LoobBackend:
    """All the logic. No tkinter here, so it can be tested without a screen."""

    def __init__(self):
        setup_folders()
        settings = load_json(SETTINGS_FILE, {})
        self.model = settings.get("model", DEFAULT_MODEL)
        self.personality = settings.get("personality", "friendly")
        self.web = settings.get("web", True)
        self.history = []
        self.claude_key = get_claude_key() or settings.get("claude_key", "")

    def save_settings(self):
        save_json(
            SETTINGS_FILE,
            {"model": self.model, "personality": self.personality, "web": self.web},
        )

    def system_prompt(self):
        text = PERSONALITIES.get(self.personality, PERSONALITIES["friendly"])
        text += (
            f" You are {NAME}, an AI assistant created and founded by {CREATOR_NAME}. "
            "If anyone asks who made you, answer with that name. Never say Meta or any "
            "other company."
        )
        text += (
            " Think step by step before answering. For maths, show the working and "
            "double-check the final answer. For code, write complete working code. "
            "Reply in the same language the user writes in."
        )
        text += f" Today is {datetime.now().strftime('%A, %d %B %Y')}."
        return text

    # ---------- web search ----------
    def web_search(self, query):
        results = ""
        try:
            from ddgs import DDGS

            found = DDGS().text(query, max_results=5)
            results = "\n".join(f"- {r['title']}: {r['body']}" for r in found)
        except ImportError:
            pass
        except Exception:
            pass
        if not results:
            results = self.wiki_search(query)
        return results

    def wiki_search(self, query):
        try:
            url = (
                "https://en.wikipedia.org/w/api.php?action=query&list=search"
                "&format=json&srlimit=4&srsearch=" + urllib.parse.quote(query)
            )
            request = urllib.request.Request(url, headers={"User-Agent": "Loob/1.0"})
            with urllib.request.urlopen(request, timeout=8) as reply:
                items = json.loads(reply.read())["query"]["search"]
            return "\n".join(
                f"- {i['title']}: {re.sub('<[^>]+>', '', i['snippet'])}" for i in items
            )
        except Exception:
            return ""

    # ---------- asking the AI ----------
    def ask(self, question, status_callback=None):
        """Returns the AI's reply as plain text. Raises on failure."""
        last_message = question
        if self.web:
            if status_callback:
                status_callback("Searching the web...")
            found = self.web_search(question)
            if found:
                last_message = (
                    f"Web search results (fresh, from the internet):\n{found}\n\n"
                    f"These results are newer than your training. Trust them over "
                    f"your memory and answer directly.\nQuestion: {question}"
                )

        chat_messages = self.history + [{"role": "user", "content": last_message}]

        if status_callback:
            status_callback("Thinking...")

        if self.model.startswith("claude"):
            answer = self._ask_claude(chat_messages)
        else:
            answer = self._ask_ollama(chat_messages)

        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def _ask_ollama(self, chat_messages):
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": self.system_prompt()}] + chat_messages,
        }
        request = urllib.request.Request(
            OLLAMA_URL + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as reply:
                data = json.loads(reply.read())
            return data["message"]["content"]
        except urllib.error.HTTPError as problem:
            if problem.code == 404:
                raise RuntimeError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
            raise RuntimeError(f"Ollama error: {problem}")
        except urllib.error.URLError:
            raise RuntimeError("Can't reach Ollama. Make sure the Ollama app is open.")

    def _ask_claude(self, chat_messages):
        key = os.environ.get("ANTHROPIC_API_KEY") or self.claude_key
        if not key:
            raise RuntimeError("No Claude key saved yet. Add one in Settings.")
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "system": self.system_prompt(),
            "messages": chat_messages,
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as reply:
                data = json.loads(reply.read())
            return "".join(block.get("text", "") for block in data.get("content", []))
        except urllib.error.HTTPError as problem:
            detail = problem.read().decode("utf-8", "ignore")[:300]
            raise RuntimeError(f"Claude error {problem.code}: {detail}")
        except Exception as problem:
            raise RuntimeError(f"Could not reach Claude: {problem}")

    # ---------- images ----------
    def image_url(self, prompt):
        return (
            "https://image.pollinations.ai/prompt/"
            + urllib.parse.quote(prompt)
            + f"?width=768&height=768&nologo=true&seed={random.randint(0, 100000)}"
        )

    def download_image(self, prompt):
        """Returns the raw image bytes. Raises a clear error if it fails."""
        url = self.image_url(prompt)
        request = urllib.request.Request(url, headers={"User-Agent": "Loob/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=90) as reply:
                data = reply.read()
        except urllib.error.URLError as problem:
            raise RuntimeError(
                "Could not reach the image website. This is usually your internet "
                "or firewall blocking it, not a bug in Loob. Try again, or try on a "
                f"different internet connection. ({problem})"
            )
        if not data:
            raise RuntimeError("The image website sent back nothing. Please try again.")
        return data

    # ---------- chats ----------
    def save_chat(self, name=None):
        if not self.history:
            return None
        name = name or datetime.now().strftime("chat_%Y%m%d_%H%M%S")
        path = os.path.join(CHAT_DIR, name + ".json")
        save_json(path, self.history)
        return name

    def list_chats(self):
        return sorted(f[:-5] for f in os.listdir(CHAT_DIR) if f.endswith(".json"))

    def load_chat(self, name):
        path = os.path.join(CHAT_DIR, name + ".json")
        data = load_json(path, None)
        if data is not None:
            self.history = data
        return data is not None


# ----------------------------------------------------------------------
# Window - everything the person actually sees and clicks.
# ----------------------------------------------------------------------
class LoobApp:
    # A deliberate color palette, not tkinter's grey defaults.
    COLORS = {
        "bg": "#13111f",           # deep indigo-black page background
        "panel": "#1d1a2e",        # slightly lighter panel strip
        "gradient_start": "#6366f1",  # indigo
        "gradient_end": "#a855f7",    # violet
        "user_bubble": "#6366f1",
        "user_text": "#ffffff",
        "bot_bubble": "#262244",
        "bot_text": "#f1f0fb",
        "status_text": "#9a94c2",
        "entry_bg": "#262244",
        "entry_fg": "#ffffff",
        "accent": "#8b5cf6",
    }

    def __init__(self, root):
        self.root = root
        self.backend = LoobBackend()
        self.image_refs = []  # keeps images from being garbage-collected

        root.title("Loob")
        root.geometry("560x720")
        root.configure(bg=self.COLORS["bg"])

        self._build_menu()
        self._build_header()
        self._build_chat_area()
        self._build_input_row()
        self._build_status_bar()

        if not PIL_OK:
            self.show_status("Tip: run 'pip install pillow' to see pictures in the chat.")
        self.show_status(f"Model: {self.backend.model}  |  Personality: {self.backend.personality}")

    # ---------- building the window ----------
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        chat_menu = tk.Menu(menubar, tearoff=0)
        chat_menu.add_command(label="New chat", command=self.new_chat)
        chat_menu.add_command(label="Save chat", command=self.save_chat)
        chat_menu.add_command(label="Load chat...", command=self.load_chat_dialog)
        menubar.add_cascade(label="Chat", menu=chat_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Choose mode / model...", command=self.choose_mode)
        settings_menu.add_command(label="Choose personality...", command=self.choose_personality)
        settings_menu.add_command(label="Set Claude API key...", command=self.set_key_dialog)
        self.web_var = tk.BooleanVar(value=self.backend.web)
        settings_menu.add_checkbutton(
            label="Search the web for fresh facts", variable=self.web_var, command=self.toggle_web
        )
        menubar.add_cascade(label="Settings", menu=settings_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Generate an image...", command=self.image_dialog)
        tools_menu.add_command(label="Search videos on YouTube...", command=self.video_dialog)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        self.root.config(menu=menubar)

    def _build_header(self):
        """A colorful gradient banner with the app name - purely decorative,
        the real menu above it still does the work."""
        self.header_height = 70
        self.header_canvas = tk.Canvas(
            self.root, height=self.header_height, highlightthickness=0, bd=0
        )
        self.header_canvas.pack(fill="x")
        self.header_canvas.bind("<Configure>", self._redraw_header)

    def _redraw_header(self, event=None):
        canvas = self.header_canvas
        width = event.width if event else canvas.winfo_width()
        if width < 2:
            return
        canvas.delete("all")
        self._draw_gradient(
            canvas, width, self.header_height,
            self.COLORS["gradient_start"], self.COLORS["gradient_end"],
        )
        canvas.create_text(
            20, self.header_height // 2, text="✨ Loob", anchor="w",
            fill="white", font=("Segoe UI", 20, "bold"),
        )
        canvas.create_text(
            width - 20, self.header_height // 2, text="your own AI", anchor="e",
            fill="#e9e6ff", font=("Segoe UI", 10),
        )

    @staticmethod
    def _draw_gradient(canvas, width, height, color1, color2):
        """Paints a smooth left-to-right color gradient on a Canvas."""
        r1, g1, b1 = canvas.winfo_rgb(color1)
        r2, g2, b2 = canvas.winfo_rgb(color2)
        steps = max(width, 1)
        r_step = (r2 - r1) / steps
        g_step = (g2 - g1) / steps
        b_step = (b2 - b1) / steps
        for i in range(steps):
            nr = int(r1 + r_step * i) >> 8
            ng = int(g1 + g_step * i) >> 8
            nb = int(b1 + b_step * i) >> 8
            canvas.create_line(i, 0, i, height, fill=f"#{nr:02x}{ng:02x}{nb:02x}")

    def _build_chat_area(self):
        outer = tk.Frame(self.root, bg=self.COLORS["bg"])
        outer.pack(fill="both", expand=True)

        self.chat_canvas = tk.Canvas(outer, bg=self.COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.chat_canvas.pack(side="left", fill="both", expand=True)

        self.chat_frame = tk.Frame(self.chat_canvas, bg=self.COLORS["bg"])
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")

        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")),
        )
        self.chat_canvas.bind(
            "<Configure>",
            lambda e: self.chat_canvas.itemconfig(self.chat_window, width=e.width),
        )
        self.chat_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.chat_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.chat_canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            self.chat_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or getattr(event, "delta", 0) < 0:
            self.chat_canvas.yview_scroll(1, "units")

    def _scroll_to_bottom(self):
        self.root.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _build_input_row(self):
        row = tk.Frame(self.root, bg=self.COLORS["panel"])
        row.pack(fill="x", side="bottom")

        inner = tk.Frame(row, bg=self.COLORS["panel"])
        inner.pack(fill="x", padx=12, pady=12)

        self.entry = tk.Entry(
            inner, font=("Segoe UI", 11), bg=self.COLORS["entry_bg"],
            fg=self.COLORS["entry_fg"], insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=self.COLORS["accent"], highlightcolor=self.COLORS["accent"],
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=10)
        self.entry.bind("<Return>", lambda event: self.send())
        self.entry.focus()

        tk.Button(
            inner, text="Send", command=self.send, bg=self.COLORS["accent"], fg="white",
            activebackground=self.COLORS["gradient_start"], activeforeground="white",
            relief="flat", font=("Segoe UI", 10, "bold"), padx=16, pady=6, bd=0,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

    def _build_status_bar(self):
        self.status_label = tk.Label(
            self.root, text="", bg=self.COLORS["panel"], fg=self.COLORS["status_text"],
            anchor="w", font=("Segoe UI", 9),
        )
        self.status_label.pack(fill="x", side="bottom", padx=12, pady=(0, 6))

    # ---------- writing to the chat area (colorful bubbles) ----------
    def show_message(self, text, who):
        """who is 'user' or 'bot' - draws a colored, aligned chat bubble."""
        row = tk.Frame(self.chat_frame, bg=self.COLORS["bg"])
        row.pack(fill="x", padx=14, pady=5)

        bubble_bg = self.COLORS["user_bubble"] if who == "user" else self.COLORS["bot_bubble"]
        bubble_fg = self.COLORS["user_text"] if who == "user" else self.COLORS["bot_text"]
        side = "right" if who == "user" else "left"

        bubble = tk.Label(
            row, text=text, bg=bubble_bg, fg=bubble_fg, font=("Segoe UI", 11),
            wraplength=340, justify="left", padx=14, pady=10, bd=0,
        )
        bubble.pack(side=side)
        self._scroll_to_bottom()

    def show_status(self, text):
        self.status_label.config(text=text)
        if text:
            row = tk.Frame(self.chat_frame, bg=self.COLORS["bg"])
            row.pack(fill="x", pady=3)
            tk.Label(
                row, text=text, bg=self.COLORS["bg"], fg=self.COLORS["status_text"],
                font=("Segoe UI", 9, "italic"),
            ).pack()
            self._scroll_to_bottom()

    def show_image_bytes(self, image_bytes, caption):
        if not PIL_OK:
            self.show_message(f"({caption} - install 'pillow' to see pictures)", "bot")
            return
        image = Image.open(io.BytesIO(image_bytes))
        image.thumbnail((360, 360))
        photo = ImageTk.PhotoImage(image)
        self.image_refs.append(photo)  # keep a reference so it isn't erased

        row = tk.Frame(self.chat_frame, bg=self.COLORS["bg"])
        row.pack(fill="x", padx=14, pady=5, anchor="w")
        card = tk.Frame(row, bg=self.COLORS["bot_bubble"], padx=6, pady=6)
        card.pack(side="left")
        tk.Label(card, image=photo, bg=self.COLORS["bot_bubble"]).pack()
        tk.Label(
            card, text=caption, bg=self.COLORS["bot_bubble"], fg=self.COLORS["status_text"],
            font=("Segoe UI", 9), wraplength=340,
        ).pack(pady=(4, 0))
        self._scroll_to_bottom()

    # ---------- sending a message ----------
    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.show_message("You: " + text, "user")

        if is_creator_question(text):
            self.show_image_bytes(creator_image_bytes(), f"Created by {CREATOR_NAME}")
            return

        if text.lower().startswith("/image "):
            prompt = text[7:].strip()
            if prompt:
                self.show_status("Generating image... this can take up to a minute, please wait.")
                threading.Thread(target=self._image_worker, args=(prompt,), daemon=True).start()
            return

        self.show_status("Working...")
        threading.Thread(target=self._ask_worker, args=(text,), daemon=True).start()

    def _ask_worker(self, question):
        # status_callback runs on a background thread, so hand its updates to
        # the main thread via root.after - tkinter widgets aren't thread-safe.
        safe_status = lambda text: self.root.after(0, lambda: self.show_status(text))
        try:
            answer = self.backend.ask(question, status_callback=safe_status)
            self.root.after(0, lambda: self._ask_done(answer, None))
        except Exception as problem:
            self.root.after(0, lambda: self._ask_done(None, str(problem)))

    def _ask_done(self, answer, error_text):
        self.status_label.config(text="")
        if error_text:
            self.show_status(f"({error_text})")
        else:
            self.show_message(f"{NAME}: {answer}", "bot")

    # ---------- menu actions ----------
    def new_chat(self):
        self.backend.history = []
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.show_status("Started a fresh chat.")

    def save_chat(self):
        name = self.backend.save_chat()
        self.show_status(f"Saved as '{name}'." if name else "Nothing to save yet.")

    def load_chat_dialog(self):
        chats = self.backend.list_chats()
        if not chats:
            messagebox.showinfo("Loob", "No saved chats yet.")
            return
        name = simpledialog.askstring(
            "Load chat", "Chats available:\n" + "\n".join(chats) + "\n\nType a name:"
        )
        if name and self.backend.load_chat(name):
            self.new_chat()
            for message in self.backend.history:
                who = "You" if message["role"] == "user" else NAME
                self.show_message(f"{who}: {message['content']}", "bot")
        elif name:
            messagebox.showerror("Loob", f"No chat called '{name}'.")

    def choose_mode(self):
        choice = simpledialog.askstring(
            "Choose mode",
            "Type one of:\n" + "\n".join(MODES) + "\n\n(Needs: ollama pull <model>, except Claude)",
        )
        if choice and choice in MODES:
            self.backend.model = MODES[choice]
            self.backend.save_settings()
            self.show_status(f"Now using: {choice} ({self.backend.model})")
        elif choice:
            messagebox.showerror("Loob", "Not a valid choice. Open the menu again to see options.")

    def choose_personality(self):
        choice = simpledialog.askstring(
            "Choose personality", "Type one of:\n" + "\n".join(PERSONALITIES)
        )
        if choice and choice in PERSONALITIES:
            self.backend.personality = choice
            self.backend.save_settings()
            self.show_status(f"Personality: {choice}")
        elif choice:
            messagebox.showerror("Loob", "Not a valid choice.")

    def set_key_dialog(self):
        key = simpledialog.askstring("Claude API key", "Paste your key from console.anthropic.com:", show="*")
        if key:
            self.backend.claude_key = key
            if set_claude_key(key):
                messagebox.showinfo("Loob", "Key saved securely.")
            else:
                messagebox.showwarning("Loob", "Install 'keyring' for secure storage: pip install keyring")

    def toggle_web(self):
        self.backend.web = self.web_var.get()
        self.backend.save_settings()
        self.show_status("Web search is now " + ("on" if self.backend.web else "off") + ".")

    def image_dialog(self):
        prompt = simpledialog.askstring("Generate image", "Describe the picture:")
        if not prompt:
            return
        self.show_message("You: /image " + prompt, "user")
        self.show_status("Generating image... this can take up to a minute, please wait.")
        threading.Thread(target=self._image_worker, args=(prompt,), daemon=True).start()

    def _image_worker(self, prompt):
        try:
            data = self.backend.download_image(prompt)
            self.root.after(0, lambda: self._image_done(data, prompt, None))
        except Exception as problem:
            self.root.after(0, lambda: self._image_done(None, prompt, str(problem)))

    def _image_done(self, data, prompt, error_text):
        self.status_label.config(text="")
        if error_text:
            self.show_status(f"(Could not generate the image: {error_text})")
        else:
            self.show_image_bytes(data, prompt)

    def video_dialog(self):
        import webbrowser

        topic = simpledialog.askstring("Search videos", "What should Loob search for on YouTube?")
        if topic:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(topic)
            webbrowser.open(url)
            self.show_status(f"Opened YouTube search for '{topic}'.")


if __name__ == "__main__":
    root = tk.Tk()
    app = LoobApp(root)
    root.mainloop()