SI = ((10**3, "k"),
      (10**6, "M"),
      (10**9, "G"),
      (10**12, "T"),
      (10**15, "P"),
      (10**18, "E"),
      (10**21, "Z"),
      (10**24, "Y"))

def str_SI(no):
    if no==None: return str(no)
    if type(no)==type(""):
        if no.startswith("depth"):
            return no
        no = int(no)
    last_unit = ""
    last_mag = 1
    for i in range(len(SI)):
        mag, unit = SI[i]
        if no<mag or no%mag: return "%i%s" % (no//last_mag, last_unit)
        last_mag, last_unit  = mag, unit
    return "%i%s" % (no//last_mag, last_unit)

