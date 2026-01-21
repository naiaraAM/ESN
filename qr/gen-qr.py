import segno

qrcode = segno.make_qr("https://esnsantander.org/esncard")
qrcode.save(
    "esncard_qrcode.png",
    scale=100,
)