// QUARTET - Logic-based S-box (ANF) for synthesis estimation
// PRESENT S-box ANF from cipher.py sbox_bitsliced
module sbox4_logic (
    input  [3:0] a,
    output [3:0] y
);
    wire x0 = a[0], x1 = a[1], x2 = a[2], x3 = a[3];
    wire t1 = x0 & x1;
    wire t2 = x0 & x2;
    wire t3 = x0 & x3;
    wire t4 = x1 & x2;
    wire t5 = x1 & x3;
    wire t6 = x2 & x3;
    wire t7 = t1 & x2;
    wire t8 = t1 & x3;
    wire t9 = t2 & x3;

    assign y[0] = x0 ^ x2 ^ t4 ^ x3;
    assign y[1] = x1 ^ x3 ^ t5 ^ t6 ^ t7 ^ t8 ^ t9;
    assign y[2] = 1'b1 ^ x2 ^ x3 ^ t1 ^ t3 ^ t5 ^ t8 ^ t9;
    assign y[3] = 1'b1 ^ x0 ^ x1 ^ x3 ^ t4 ^ t7 ^ t8 ^ t9;
endmodule

module fullmix (
    input  [15:0] din,
    output [15:0] dout
);
    wire [3:0] w0 = din[15:12];
    wire [3:0] w1 = din[11:8];
    wire [3:0] w2 = din[7:4];
    wire [3:0] w3 = din[3:0];
    assign dout = {w0 ^ w1 ^ w2, w1 ^ w2 ^ w3, w2 ^ w3 ^ w0, w3 ^ w0 ^ w1};
endmodule

module quartet_round_logic (
    input  [15:0] din,
    input  [3:0]  rk,
    output [15:0] dout
);
    wire [3:0] s0, s1, s2, s3;
    sbox4_logic s0i (.a(din[15:12]), .y(s0));
    sbox4_logic s1i (.a(din[11:8]),  .y(s1));
    sbox4_logic s2i (.a(din[7:4]),   .y(s2));
    sbox4_logic s3i (.a(din[3:0]),   .y(s3));
    wire [15:0] mid = {s0 ^ rk, s1 ^ rk, s2 ^ rk, s3 ^ rk};
    fullmix fm (.din(mid), .dout(dout));
endmodule

module quartet_enc_unrolled_logic (
    input  [15:0] plaintext,
    input  [63:0] key, // not used in datapath area, key schedule separate
    output [15:0] ciphertext
);
    // 16 rounds unrolled with dummy fixed rk for datapath area only
    // For fair GE we measure single round * 16 or iteractive
    wire [15:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16;
    assign s0 = plaintext;
    quartet_round_logic r0 (.din(s0),  .rk(key[3:0]),   .dout(s1));
    quartet_round_logic r1 (.din(s1),  .rk(key[7:4]),   .dout(s2));
    quartet_round_logic r2 (.din(s2),  .rk(key[11:8]),  .dout(s3));
    quartet_round_logic r3 (.din(s3),  .rk(key[15:12]), .dout(s4));
    quartet_round_logic r4 (.din(s4),  .rk(key[19:16]), .dout(s5));
    quartet_round_logic r5 (.din(s5),  .rk(key[23:20]), .dout(s6));
    quartet_round_logic r6 (.din(s6),  .rk(key[27:24]), .dout(s7));
    quartet_round_logic r7 (.din(s7),  .rk(key[31:28]), .dout(s8));
    quartet_round_logic r8 (.din(s8),  .rk(key[35:32]), .dout(s9));
    quartet_round_logic r9 (.din(s9),  .rk(key[39:36]), .dout(s10));
    quartet_round_logic r10(.din(s10), .rk(key[43:40]), .dout(s11));
    quartet_round_logic r11(.din(s11), .rk(key[47:44]), .dout(s12));
    quartet_round_logic r12(.din(s12), .rk(key[51:48]), .dout(s13));
    quartet_round_logic r13(.din(s13), .rk(key[55:52]), .dout(s14));
    quartet_round_logic r14(.din(s14), .rk(key[59:56]), .dout(s15));
    quartet_round_logic r15(.din(s15), .rk(key[63:60]), .dout(s16));
    assign ciphertext = s16;
endmodule

// Iterative core with single round datapath
module quartet_iter_logic (
    input clk, rst, start,
    input [15:0] plaintext,
    input [63:0] key,
    output reg [15:0] ciphertext,
    output reg done
);
    reg [15:0] state;
    reg [4:0] round;
    wire [3:0] rk = key[round*4 +: 4]; // simplified key schedule for area (actual is larger)
    wire [15:0] next_state;
    quartet_round_logic rnd (.din(state), .rk(rk), .dout(next_state));
    always @(posedge clk or posedge rst) begin
        if (rst) begin state<=0; round<=0; done<=0; ciphertext<=0; end
        else if (start) begin state<=plaintext; round<=0; done<=0; end
        else if (round < 16) begin
            state <= next_state;
            round <= round+1;
            if (round==15) begin ciphertext<=next_state; done<=1; end
        end
    end
endmodule
