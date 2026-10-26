#!/usr/bin/env python3
"""Generate rtl/c128_keyboard_sym.sv: symbolic PS/2 keyboard layouts for the C128.

With the OSD's "Keyboard Layout" set to US, UK or DE, the character printed
on the host key cap is what the C128 (or C64 mode) gets: the SHIFT key is
pressed or released behind the scenes where the two keyboards disagree (":"
is Shift+";" on a PC but its own key on a C128, '"' is Shift+2 on a C128 but
Shift+' on a US PC).  "Original" keeps fpga64_keyboard's own mapping.

Only the character keys are taken over: the digit and symbol keys (and Y / Z
for DE), F9 / F10 (up arrow, "="), and in C64 mode the numeric keypad, which
fpga64_keyboard maps to the main keys there.  Every other key, including the
C128's extra keys, the Fn layer (AltGr) and the keypad in C128 mode, stays
with fpga64_keyboard; owns tells it which PS/2 keys to leave alone.

Adapted from scripts/gen_keyboard.py of the C65 MiSTer core.
"""
import os

# ---------------------------------------------------------------- matrix
# the C64 / C128 8x8 matrix: index = column * 8 + row (columns = CIA1 PA bits)
MATRIX = [
    ["DEL", "RETURN", "RIGHT", "F7", "F1", "F3", "F5", "DOWN"],
    ["3", "W", "A", "4", "Z", "S", "E", "LSHIFT"],
    ["5", "R", "D", "6", "C", "F", "T", "X"],
    ["7", "Y", "G", "8", "B", "H", "U", "V"],
    ["9", "I", "J", "0", "M", "K", "O", "N"],
    ["PLUS", "P", "L", "MINUS", "DOT", "COLON", "AT", "COMMA"],
    ["POUND", "STAR", "SEMI", "HOME", "RSHIFT", "EQUAL", "UPARROW", "SLASH"],
    ["1", "LEFTARROW", "CTRL", "2", "SPACE", "CBM", "Q", "STOP"],
]
KEY = {n: c * 8 + r for c, col in enumerate(MATRIX) for r, n in enumerate(col)}

# the matrix keys this module drives (fpga64_keyboard takes them from keys_out)
OWNED = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "PLUS", "MINUS", "AT", "STAR", "EQUAL",
         "COLON", "SEMI", "COMMA", "DOT", "SLASH", "POUND", "UPARROW", "LEFTARROW", "Y", "Z"]

ASIS, OFF, ON = 0, 1, 2      # what to do with SHIFT while held

# symbol name -> (matrix key, shift handling)
SYM = {
    "EXCL": ("1", ON), "DQUOTE": ("2", ON), "HASH": ("3", ON), "DOLLAR": ("4", ON), "PERCENT": ("5", ON),
    "AMP": ("6", ON), "QUOTE": ("7", ON), "LPAREN": ("8", ON), "RPAREN": ("9", ON),
    "PLUS": ("PLUS", OFF), "MINUS": ("MINUS", OFF), "AT": ("AT", OFF), "STAR": ("STAR", OFF),
    "EQUAL": ("EQUAL", OFF), "COLON": ("COLON", OFF), "SEMI": ("SEMI", OFF), "COMMA": ("COMMA", OFF),
    "DOT": ("DOT", OFF), "SLASH": ("SLASH", OFF), "LESS": ("COMMA", ON), "GREATER": ("DOT", ON),
    "QUESTION": ("SLASH", ON), "LBRACKET": ("COLON", ON), "RBRACKET": ("SEMI", ON),
    "CARET": ("UPARROW", OFF), "PI": ("UPARROW", ON), "POUND": ("POUND", OFF),
    "LEFTARROW": ("LEFTARROW", OFF), "UNDERSCORE": ("LEFTARROW", OFF), "BACKSLASH": ("POUND", OFF),
    "BAR": ("POUND", ON),
}
for d in "0123456789":
    SYM["D" + d] = (d, OFF)

# keys taken over in both modes: code -> (matrix key, shift handling)
COMMON = {
    0x01: ("UPARROW", ASIS),     # F9
    0x09: ("EQUAL", ASIS),       # F10
}
# C64 mode only: fpga64_keyboard puts the keypad on the main keys there
PURE64 = {
    0x70: ("0", OFF), 0x69: ("1", OFF), 0x72: ("2", OFF), 0x7A: ("3", OFF), 0x6B: ("4", OFF), 0x73: ("5", OFF),
    0x74: ("6", OFF), 0x6C: ("7", OFF), 0x75: ("8", OFF), 0x7D: ("9", OFF), 0x71: ("DOT", OFF),
    0x79: ("PLUS", OFF), 0x7B: ("MINUS", OFF), 0x7C: ("STAR", OFF), 0x14A: ("SLASH", OFF),
    0x17A: ("UPARROW", ASIS),    # PgDn
}

# symbol keys per layout: code -> (unshifted symbol, shifted symbol)
US = {
    0x0E: ("LEFTARROW", "PI"), 0x16: ("D1", "EXCL"), 0x1E: ("D2", "AT"), 0x26: ("D3", "HASH"),
    0x25: ("D4", "DOLLAR"), 0x2E: ("D5", "PERCENT"), 0x36: ("D6", "CARET"), 0x3D: ("D7", "AMP"),
    0x3E: ("D8", "STAR"), 0x46: ("D9", "LPAREN"), 0x45: ("D0", "RPAREN"), 0x4E: ("MINUS", "UNDERSCORE"),
    0x55: ("EQUAL", "PLUS"), 0x54: ("LBRACKET", "LBRACKET"), 0x5B: ("RBRACKET", "RBRACKET"),
    0x5D: ("BACKSLASH", "BAR"), 0x4C: ("SEMI", "COLON"), 0x52: ("QUOTE", "DQUOTE"),
    0x41: ("COMMA", "LESS"), 0x49: ("DOT", "GREATER"), 0x4A: ("SLASH", "QUESTION"),
}
UK = dict(US)
UK.update({
    0x1E: ("D2", "DQUOTE"), 0x26: ("D3", "POUND"), 0x52: ("QUOTE", "AT"),
    0x5D: ("HASH", "PI"), 0x61: ("BACKSLASH", "BAR"),
})
DE = {
    0x0E: ("CARET", "PI"), 0x16: ("D1", "EXCL"), 0x1E: ("D2", "DQUOTE"), 0x26: ("D3", "AT"),
    0x25: ("D4", "DOLLAR"), 0x2E: ("D5", "PERCENT"), 0x36: ("D6", "AMP"), 0x3D: ("D7", "SLASH"),
    0x3E: ("D8", "LPAREN"), 0x46: ("D9", "RPAREN"), 0x45: ("D0", "EQUAL"), 0x4E: ("POUND", "QUESTION"),
    0x55: ("QUOTE", "LEFTARROW"), 0x54: ("AT", "AT"), 0x5B: ("PLUS", "STAR"), 0x5D: ("HASH", "QUOTE"),
    0x4C: ("LBRACKET", "LBRACKET"), 0x52: ("RBRACKET", "RBRACKET"), 0x61: ("LESS", "GREATER"),
    0x41: ("COMMA", "SEMI"), 0x49: ("DOT", "COLON"), 0x4A: ("MINUS", "UNDERSCORE"),
}
LAYOUTS = (("US", US), ("UK", UK), ("DE", DE))     # OSD values 1, 2, 3


def build(name, table, pure64):
    """return {(shift, code): (key index, mode)}"""
    t = {}
    keys = dict(COMMON)
    if pure64:
        keys.update(PURE64)
    for sh in (0, 1):
        for code, (k, m) in keys.items():
            t[(sh, code)] = (KEY[k], m)
        # Y and Z: swapped on a German keyboard
        for code, letter in ((0x35, "Y"), (0x1A, "Z")):
            if name == "DE":
                letter = "Z" if letter == "Y" else "Y"
            t[(sh, code)] = (KEY[letter], ASIS)
    for code, syms in table.items():
        for sh in (0, 1):
            k, m = SYM[syms[sh]]
            # only force the shift state where it differs from the host's
            if (m == ON and sh == 1) or (m == OFF and sh == 0):
                m = ASIS
            t[(sh, code)] = (KEY[k], m)
    for (sh, code), (k, m) in t.items():
        assert any(KEY[o] == k for o in OWNED), (name, hex(code), k)
    return t


HEADER = '''// Symbolic PS/2 keyboard layouts for the C128 (OSD "Keyboard Layout").
// GENERATED by scripts/gen_keyboard_sym.py -- edit the tables there.
//
// layout: 1 = US, 2 = UK, 3 = DE: the character on the host key cap is what
// the C128 sees, SHIFT being pressed or released behind the scenes where the
// keyboards disagree.  Only the character keys are handled here (digits,
// symbols, Y / Z, F9 / F10, and the keypad in C64 mode): owns is set for the
// PS/2 key on ps2_key when this module takes it, and fpga64_keyboard then
// leaves it alone and reads those matrix keys from keys_out (1 = pressed,
// index = PA bit * 8 + PB bit).  shift_off / shift_on release or press SHIFT
// for them.  With layout 0 nothing is taken over.
//
// Adapted from the C65 MiSTer core's keyboard (rtl/c65_keyboard.sv).

module c128_keyboard_sym (
	input  logic        clk,
	input  logic        reset,
	input  logic  [1:0] layout,
	input  logic        pure64,      // C64 mode: the keypad is taken over as well
	input  logic [10:0] ps2_key,     // [10] toggles on event, [9] pressed, [8] extended, [7:0] code
	output logic [63:0] keys_out,
	output logic        shift_off,
	output logic        shift_on,
	output logic        owns
);

localparam logic [5:0] K_LSHIFT = 6'd%d;
localparam logic [5:0] K_RSHIFT = 6'd%d;

// {valid, shift handling, key}: handling 0 = leave SHIFT alone, 1 = release it, 2 = press it
function automatic [8:0] keymap(input logic [1:0] lay, input logic p64, input logic shift, input logic [8:0] code);
	keymap = 9'd0;
	case ({lay, p64, shift, code})
'''

FOOTER = '''		default: ;
	endcase
endfunction

logic [63:0] keys;        // 1 = pressed
logic [63:0] f_on, f_off; // held keys that force the SHIFT state
logic        ps2_stb;
logic        host_shift_l, host_shift_r;

// A key that changes the SHIFT state must not meet a keyboard scan that is
// half done: the KERNAL could read SHIFT before the change and the key after
// it (shift+":" = "[").  So the new key is kept out of the matrix for ~2 ms
// after the SHIFT change (longer than one scan), and on release the SHIFT
// override is kept for ~2 ms after the key has gone.
logic [63:0] hold;        // pressed, not yet visible
logic        lin_off, lin_on;
logic [16:0] hold_cnt, lin_cnt;

wire       host_shift = host_shift_l | host_shift_r;
wire [8:0] m_now = keymap(layout, pure64, host_shift, ps2_key[8:0]);
wire [8:0] m_s0  = keymap(layout, pure64, 1'b0, ps2_key[8:0]);
wire [8:0] m_s1  = keymap(layout, pure64, 1'b1, ps2_key[8:0]);

assign owns = m_s0[8] | m_s1[8];

always_ff @(posedge clk) begin
	ps2_stb <= ps2_key[10];
	if (reset) begin
		keys <= '0; f_on <= '0; f_off <= '0; host_shift_l <= 1'b0; host_shift_r <= 1'b0;
		hold <= '0; lin_off <= 1'b0; lin_on <= 1'b0; hold_cnt <= '0; lin_cnt <= '0;
	end
	else begin
		if (hold_cnt != 0) hold_cnt <= hold_cnt - 1'd1; else hold <= '0;
		if (lin_cnt != 0)  lin_cnt  <= lin_cnt - 1'd1;  else begin lin_off <= 1'b0; lin_on <= 1'b0; end
		if (ps2_stb != ps2_key[10]) begin
			if (ps2_key[8:0] == 9'h012) host_shift_l <= ps2_key[9];
			if (ps2_key[8:0] == 9'h059) host_shift_r <= ps2_key[9];
			if (ps2_key[9]) begin
				if (m_now[8]) begin
					keys[m_now[5:0]]  <= 1'b1;
					f_off[m_now[5:0]] <= (m_now[7:6] == 2'd1);
					f_on[m_now[5:0]]  <= (m_now[7:6] == 2'd2);
					if (m_now[7:6] != 2'd0) begin hold[m_now[5:0]] <= 1'b1; hold_cnt <= 17'd65535; end
				end
			end
			else begin
				// the shift state may have changed since the press: release both candidates
				if (m_s0[8]) begin keys[m_s0[5:0]] <= 1'b0; f_off[m_s0[5:0]] <= 1'b0; f_on[m_s0[5:0]] <= 1'b0; hold[m_s0[5:0]] <= 1'b0; end
				if (m_s1[8]) begin keys[m_s1[5:0]] <= 1'b0; f_off[m_s1[5:0]] <= 1'b0; f_on[m_s1[5:0]] <= 1'b0; hold[m_s1[5:0]] <= 1'b0; end
				if ((m_s0[8] && (f_off[m_s0[5:0]] || f_on[m_s0[5:0]])) || (m_s1[8] && (f_off[m_s1[5:0]] || f_on[m_s1[5:0]]))) begin
					lin_off <= (m_s0[8] && f_off[m_s0[5:0]]) || (m_s1[8] && f_off[m_s1[5:0]]);
					lin_on  <= (m_s0[8] && f_on[m_s0[5:0]])  || (m_s1[8] && f_on[m_s1[5:0]]);
					lin_cnt <= 17'd65535;
				end
			end
		end
	end
end

assign keys_out  = keys & ~hold;
assign shift_off = |f_off || lin_off;
assign shift_on  = !shift_off && (|f_on || lin_on);

endmodule
'''


def main():
    names = {v: k for k, v in KEY.items()}
    out = [HEADER % (KEY["LSHIFT"], KEY["RSHIFT"])]
    for li, (lay, table) in enumerate(LAYOUTS, start=1):
        for p64 in (0, 1):
            out.append("\t\t// ---- layout %d: %s%s\n" % (li, lay, " (C64 mode)" if p64 else ""))
            t = build(lay, table, p64)
            for (sh, code) in sorted(t, key=lambda x: (x[1], x[0])):
                idx, mode = t[(sh, code)]
                out.append("\t\t{2'd%d, 1'b%d, 1'b%d, 9'h%03X}: keymap = {1'b1, 2'd%d, 6'd%d};   // %s%s\n" % (
                    li, p64, sh, code, mode, idx, names[idx], ("", " (shift off)", " (shift on)")[mode]))
    out.append(FOOTER)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rtl", "c128_keyboard_sym.sv")
    open(path, "w", newline="\n").write("".join(out))
    print("owned matrix keys:", ", ".join("%s=%d" % (o, KEY[o]) for o in OWNED))


if __name__ == "__main__":
    main()
