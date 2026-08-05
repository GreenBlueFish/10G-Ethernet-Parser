module token_async_fifo #(
	parameter DATA_W = 32,
	parameter FIFO_DEPTH = 8
)(
	//Write-Side
	input                     wclk, 	//write clock
	input                     wrst_n, 	//active-low synchronous reset (write clock)
	input reg                 w_en,		//write enable
	input reg [DATA_W-1:0]    wdata_in,  //write data
	output reg                wfull,	//fifo full

	//Read-Side
	input reg                 rclk, 	//read clock
	input reg                 rrst_n,	//active-low synchronour reset (read clock)
	input reg                 r_en, 	//read enable
    output reg [DATA_W-1:0]   rdata_out, //read data
	output reg                rempty	//fifo empty
);

//----------------------------
// SET UP
//----------------------------
//Memory FIFO
reg [DATA_W-1:0] FIFO [FIFO_DEPTH-1:0];

//----------------------------
// Implementation
//----------------------------

//Write Pointer Handler
//Token ring for writes
reg [FIFO_DEPTH-1:0] w_ring;
always @(posedge wclk or negedge wrst_n) begin
	if(w_en) begin
		if(!wrst_n) begin
			w_ring <= {1'b1, {(FIFO_DEPTH-2){1'b0}}, 1'b1};
			wfull <= 1'b0;
		end else if (!wfull) begin
			//if w_ptr + 1 == r_ptr -> raise full flag on wclk
			if({w_ring[FIFO_DEPTH-2:0], w_ring[FIFO_DEPTH-1]} == r_ring) begin
			//if({w_ring == r_ring}) begin
				wfull <= 1'b1;
			end  
		
			w_ring <= {w_ring[FIFO_DEPTH-2:0], w_ring[FIFO_DEPTH-1]};

			//Writing data
			case(w_ring)
				8'b10000001: FIFO[0] <= wdata_in;
				8'b00000011: FIFO[1] <= wdata_in;
				8'b00000110: FIFO[2] <= wdata_in;
				8'b00001100: FIFO[3] <= wdata_in;
				8'b00011000: FIFO[4] <= wdata_in;
				8'b00110000: FIFO[5] <= wdata_in;
				8'b01100000: FIFO[6] <= wdata_in;
				8'b11000000: FIFO[7] <= wdata_in;
				default: ;
			endcase;

			if(rempty) begin
				rempty <= 1'b0;
			end
		end
	end
end

//Read Pointer Handler
//Token ring for reads
reg [FIFO_DEPTH-1:0] r_ring;
always @(posedge rclk or negedge rrst_n) begin
	if(r_en) begin
		if(!rrst_n) begin
			r_ring <= {1'b1, {(FIFO_DEPTH-2){1'b0}}, 1'b1};
			rempty <= 1'b1; //default empty
		end else if (!rempty) begin
			// if r_ptr + 1 = w_ptr -> raise empty flag on rclk
			if({r_ring[FIFO_DEPTH-2:0], r_ring[FIFO_DEPTH-1]} == w_ring) begin
				rempty <= 1'b1;
			//end else if(r_ring == w_ring) begin
			//	rempty <= 1'b1;
			end else begin
				if(wfull) begin
					wfull <= 1'b0;
				end
			end

			r_ring <= {r_ring[FIFO_DEPTH-2:0], r_ring[FIFO_DEPTH-1]};
		end
	end
end

always @(*) begin
	//Reading data
	case(r_ring)
		8'b10000001: rdata_out = FIFO[0];
		8'b00000011: rdata_out = FIFO[1];
		8'b00000110: rdata_out = FIFO[2];
		8'b00001100: rdata_out = FIFO[3];
		8'b00011000: rdata_out = FIFO[4];
		8'b00110000: rdata_out = FIFO[5];
		8'b01100000: rdata_out = FIFO[6];
		8'b11000000: rdata_out = FIFO[7];
		default: rdata_out = 32'h0z0z0z0z;
	endcase;
end

endmodule
