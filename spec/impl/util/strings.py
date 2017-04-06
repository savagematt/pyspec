def a_or_an(s: str) -> str:
    particle = "an" if s[0] in set('AEIOUaeiou') else "a"
    return "{} {}".format(particle, s)