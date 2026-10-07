import numpy as np
import matplotlib.pyplot as plt
import argparse

def parse_naca4(code):
    """'2412' -> (m, p, t) as fractions of chord."""
    code = str(code)
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA 4-digit code must be exactly 4 digits")
    m = int(code[0]) / 100
    p = int(code[1]) / 10
    t = int(code[2:]) / 100
    if (m==0) != (p==0): 
        raise ValueError("camber and its location must both be zero or both nonzero")
    return m, p, t


def cosine_spacing(n): 
    """n points from 0-1, bunched up near the leading and trailing edges."""
    beta = np.linspace(0, np.pi, n)
    return 0.5 * (1- np.cos(beta))

def thickness(x,t): 
    """Half-thickness distribution (closed trailing edge)."""
    return 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)

def camber_line(x,m,p): 
    """Returns camber hight yc and its slope dyc/dx at each x."""
    yc = np.zeros_like(x)
    dyc = np.zeros_like(x)
    if p == 0: 
        return yc, dyc
    front = x < p
    back = ~front
    yc[front] = (m / p**2) * (2 * p * x[front] - x[front]**2)
    yc[back] = (m / (1-p)**2) * ((1 - 2*p) + 2 * p * x[back] - x[back]**2)
    dyc[front] = (2 * m / p**2) * (p - x[front])
    dyc[back] = (2 * m / (1-p)**2) * (p - x[back])
    return yc, dyc


def naca4(code, n=100):
    """Return upper/lower surface coordinates and the camber line."""
    m, p, t = parse_naca4(code)
    x = cosine_spacing(n)
    yt = thickness(x,t)
    yc, dyc = camber_line(x,m,p)
    theta = np.arctan(dyc)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    return xu, yu, xl, yl, x, yc

def plot_airfoil(code, n=100): 
    xu, yu, xl, yl, x, yc = naca4(code, n)
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(xu, yu, "b-", label="Upper Surface")
    ax.plot(xl, yl, "r-", label="Lower Surface")
    ax.plot(x, yc, "k--", label="Camber Line")
    ax.set_aspect("equal")
    ax.set_title(f"NACA {code}")
    ax.set_xlabel("x/c")
    ax.set_ylabel("y/c")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.show()
 
def get_naca_codes():
    """Ask for one or more NACA codes separated by spaces."""
    while True:
        text = input("Enter one or more NACA codes separated by spaces "
                     "(e.g. 0012 2412 4415), or 'q' to quit: ")
        if text.strip().lower() == "q":
            return None
        codes = text.split()
        if not codes:
            print("Please enter at least one code.")
            continue
        try:
            for c in codes:
                parse_naca4(c)      # raises ValueError if any code is invalid
            return codes
        except ValueError as err:
            print(f"Invalid input: {err}. Try again.")

def compare_airfoils(codes, n=100):
    """Overlay several NACA 4-digit airfoils on one plot."""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.tab10.colors

    for i, code in enumerate(codes):
        xu, yu, xl, yl, x, yc = naca4(code, n)
        color = colors[i % len(colors)]
        ax.plot(xu, yu, color=color, label=f"NACA {code}")
        ax.plot(xl, yl, color=color)               # same color, no label
        ax.plot(x, yc, color=color, ls="--", lw=0.8)  # dashed camber line

    ax.set_aspect("equal")
    ax.set_title("Airfoil comparison (dashed = camber line)")
    ax.set_xlabel("x/c")
    ax.set_ylabel("y/c")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.show()

def export_dat(code, n=100, filename=None): 
    """Write the airfoil to a .dat file and return the file name."""
    xu, yu, xl, yl, x, yc = naca4(code, n)

    xs = np.concatenate([xu[::-1], xl[1:]])
    ys = np.concatenate([yu[::-1], yl[1:]]) + 0.0

    filename = filename or f"naca{code}.dat"
    np.savetxt(filename, np.column_stack([xs, ys]),
               fmt = "%.6f", header=f"NACA {code}", comments="")
    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot or compare NACA 4-digit airfoils.")
    parser.add_argument("codes", nargs="*", help="one or more 4-digit codes, e.g. 0012 2412 4415")
    parser.add_argument("-n", "--points", type=int, default=100,
                        help="points per surface (default 100)")
    parser.add_argument("-e", "--export", action="store_true",
                        help="also write a Selig-format .dat file for each airfoil")
    args = parser.parse_args()

    codes = args.codes or get_naca_codes()
    if codes:
        try:
            for c in codes:
                parse_naca4(c)
        except ValueError as err:
            parser.error(str(err))

        if args.export:
            for c in codes:
                print(f"Saved {export_dat(c, args.points)}")

        if len(codes) == 1:
            plot_airfoil(codes[0], args.points)
        else:
            compare_airfoils(codes, args.points)


 
