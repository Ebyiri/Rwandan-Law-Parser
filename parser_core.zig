
const std = @import("std");

pub const NodeType = enum(u8) {
    BOOK = 0, PART = 1, TITLE = 2, CHAPTER = 3, SECTION = 4, ARTICLE = 5, CONTENT = 6,
};

const Node = struct {
    id: usize,
    parent_id: i32,
    node_type: NodeType,
    number: []const u8,
    index: usize,
};

fn isDigit(c: u8) bool { return c >= '0' and c <= '9'; }

fn extractNumber(data: []const u8) []const u8 {
    var end: usize = 0;
    while (end < data.len and (isDigit(data[end]) or data[end] == '.')) : (end += 1) {}
    return data[0..end];
}

fn caseInsensitiveMatch(data: []const u8, pattern: []const u8) bool {
    if (data.len < pattern.len) return false;
    for (pattern, 0..) |char, i| {
        const d = data[i];
        const upper_d = if (d >= 'a' and d <= 'z') d - 32 else d;
        const upper_p = if (char >= 'a' and char <= 'z') char - 32 else char;
        if (upper_d != upper_p) return false;
    }
    return true;
}

var output_buf: [1024 * 2048]u8 = undefined;

export fn build_ast(stream_ptr: [*]const u8, len: usize) [*]const u8 {
    const data = stream_ptr[0..len];
    var fba = std.heap.FixedBufferAllocator.init(&output_buf);
    const allocator = fba.allocator();
    var list = std.ArrayList(Node).init(allocator);

    var i: usize = 0;
    var last_parent_id: i32 = -1;

    while (i < data.len) {
        const remaining = data[i..];
        var found = false;

        const patterns = [_]struct { pat: []const u8, t: NodeType }{
            .{ .pat = "BOOK ", .t = .BOOK },
            .{ .pat = "PART ", .t = .PART },
            .{ .pat = "TITLE ", .t = .TITLE },
            .{ .pat = "CHAPTER ", .t = .CHAPTER },
            .{ .pat = "Section ", .t = .SECTION },
            .{ .pat = "Article ", .t = .ARTICLE },
        };

        inline for (patterns) |p| {
            if (!found and caseInsensitiveMatch(remaining, p.pat)) {
                const num = extractNumber(remaining[p.pat.len..]);
                list.append(.{
                    .id = list.items.len,
                    .parent_id = last_parent_id,
                    .node_type = p.t,
                    .number = num,
                    .index = i,
                }) catch {};
                if (p.t != .ARTICLE) last_parent_id = @intCast(list.items.len - 1);
                i += p.pat.len + num.len;
                found = true;
            }
        }

        if (!found) i += 1;
    }

    var out_stream = std.ArrayList(u8).init(allocator);
    std.json.stringify(.{ .status = "success", .nodes = list.items }, .{}, out_stream.writer()) catch {};
    out_stream.append(0) catch {};
    return out_stream.items.ptr;
}
