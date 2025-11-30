from .server import load_code_map, entry_matches_query, to_code_entry


def main():
    entries = load_code_map()
    print(f"Всего записей в code_map: {len(entries)}")

    if not entries:
        print("Карта пустая, проверь artifacts/code_map.yaml")
        return

    print("Пример записи:", entries[0])

    query = "service"
    matched = [e for e in entries if entry_matches_query(e, query)]
    print(f"Совпадений по '{query}': {len(matched)}")

    if matched:
        ce = to_code_entry(matched[0])
        print("Пример CodeEntry:", ce)


if __name__ == "__main__":
    main()
