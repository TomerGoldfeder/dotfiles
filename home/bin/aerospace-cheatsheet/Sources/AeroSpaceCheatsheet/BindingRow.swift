import Foundation

struct BindingRow: Identifiable, Hashable {
    let id: String
    let mode: String
    let key: String
    let command: String

    init(mode: String, key: String, command: String) {
        self.mode = mode
        self.key = key
        self.command = command
        self.id = "\(mode)|\(key)|\(command)"
    }
}

enum BindingParseError: LocalizedError {
    case fileNotFound(String)
    case unreadable(String)

    var errorDescription: String? {
        switch self {
        case .fileNotFound(let path):
            return "Config not found: \(path)"
        case .unreadable(let message):
            return message
        }
    }
}

enum BindingParser {
    static let defaultConfigPath = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent(".config/aerospace/aerospace.toml")
        .path

    static func load(from path: String = defaultConfigPath) throws -> [BindingRow] {
        guard FileManager.default.fileExists(atPath: path) else {
            throw BindingParseError.fileNotFound(path)
        }

        let text: String
        do {
            text = try String(contentsOfFile: path, encoding: .utf8)
        } catch {
            throw BindingParseError.unreadable("Could not read \(path): \(error.localizedDescription)")
        }

        return parse(text)
    }

    static func parse(_ text: String) -> [BindingRow] {
        var rows: [BindingRow] = []
        var currentMode: String?
        var index = text.startIndex

        while index < text.endIndex {
            if text[index] == "#" {
                index = skipLine(from: index, in: text)
                continue
            }

            if text[index] == "[" {
                if let headerEnd = text[index...].firstIndex(of: "]") {
                    let header = String(text[text.index(after: index)..<headerEnd]).trimmingCharacters(in: .whitespaces)
                    currentMode = modeName(from: header)
                    index = text.index(after: headerEnd)
                    continue
                }
            }

            guard currentMode != nil else {
                index = skipLine(from: index, in: text)
                continue
            }

            let lineStart = index
            let lineEnd = text[lineStart...].firstIndex(of: "\n") ?? text.endIndex
            let line = String(text[lineStart..<lineEnd]).trimmingCharacters(in: .whitespaces)
            index = lineEnd == text.endIndex ? text.endIndex : text.index(after: lineEnd)

            if line.isEmpty { continue }

            if let equalsIndex = line.firstIndex(of: "=") {
                let key = String(line[..<equalsIndex]).trimmingCharacters(in: .whitespaces)
                let rawValue = String(line[line.index(after: equalsIndex)...]).trimmingCharacters(in: .whitespaces)
                let valuePart: String
                if rawValue.hasPrefix("[") {
                    valuePart = parseArrayBlock(startingWith: rawValue, index: &index, in: text)
                } else {
                    valuePart = stripQuotes(rawValue)
                }

                if !key.isEmpty, !valuePart.isEmpty, let mode = currentMode {
                    rows.append(BindingRow(mode: mode, key: key, command: valuePart))
                }
            }
        }

        return rows
    }

    private static func modeName(from header: String) -> String? {
        let parts = header.split(separator: ".")
        guard parts.count == 3,
              parts[0] == "mode",
              parts[2] == "binding" else {
            return nil
        }
        return String(parts[1])
    }

    private static func parseArrayBlock(startingWith firstLine: String, index: inout String.Index, in text: String) -> String {
        var block = firstLine
        while !block.contains("]") && index < text.endIndex {
            let nextStart = index
            let nextEnd = text[nextStart...].firstIndex(of: "\n") ?? text.endIndex
            let nextLine = String(text[nextStart..<nextEnd])
            index = nextEnd == text.endIndex ? text.endIndex : text.index(after: nextEnd)
            block += " " + nextLine
        }

        let pattern = #"'([^']*)'"#
        guard let regex = try? NSRegularExpression(pattern: pattern) else {
            return stripQuotes(block)
        }

        let range = NSRange(block.startIndex..<block.endIndex, in: block)
        let matches = regex.matches(in: block, range: range)
        let commands = matches.compactMap { match -> String? in
            guard match.numberOfRanges > 1,
                  let commandRange = Range(match.range(at: 1), in: block) else {
                return nil
            }
            return String(block[commandRange])
        }

        return commands.joined(separator: " ; ")
    }

    private static func stripQuotes(_ value: String) -> String {
        var trimmed = value.trimmingCharacters(in: .whitespaces)
        if (trimmed.hasPrefix("'") && trimmed.hasSuffix("'")) ||
            (trimmed.hasPrefix("\"") && trimmed.hasSuffix("\"")) {
            trimmed = String(trimmed.dropFirst().dropLast())
        }
        trimmed = trimmed.trimmingCharacters(in: CharacterSet(charactersIn: ","))
        return trimmed.trimmingCharacters(in: .whitespaces)
    }

    private static func skipLine(from index: String.Index, in text: String) -> String.Index {
        guard let lineEnd = text[index...].firstIndex(of: "\n") else {
            return text.endIndex
        }
        return text.index(after: lineEnd)
    }
}
