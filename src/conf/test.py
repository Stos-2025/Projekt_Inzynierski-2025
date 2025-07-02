
from ansi2html import Ansi2HTMLConverter
conv = Ansi2HTMLConverter(inline=True)

ansi_text = "\x1b[31mBłąd \nkomp  ilacji!\x1b[0m Linia 3: coś poszło nie tak."

html = conv.convert(ansi_text, full=False)
print(html)