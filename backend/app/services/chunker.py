"""Recursive character splitting with overlap."""

SEPARATORS = ["\n\n", "\n", " ", ""]


def split_text(text: str, separator: str) -> list[str]:
    if separator == "":
        return list(text)

    return text.split(separator)


def merge_chunks(
    splits: list[str],
    separator: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:

    chunks: list[str] = []

    current = ""

    for split in splits:

        candidate = (
            current + separator + split
            if current
            else split
        )

        if len(candidate) > chunk_size and current:

            chunks.append(current)

            words = current.split(" ")

            tail = ""

            for i in range(len(words) - 1, -1, -1):

                t = words[i] + (" " + tail if tail else "")

                if len(t) > overlap:
                    break

                tail = t

            current = (
                tail + separator + split
                if tail
                else split
            )

        else:

            current = candidate

    if current.strip():
        chunks.append(current)

    return chunks


def recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    overlap: int,
) -> list[str]:

    if not separators:
        return [text]

    sep, *rest = separators

    splits = split_text(text, sep)

    good_splits: list[str] = []

    final_chunks: list[str] = []

    for split in splits:

        if len(split) <= chunk_size:

            good_splits.append(split)

        else:

            if good_splits:

                final_chunks.extend(
                    merge_chunks(
                        good_splits,
                        sep,
                        chunk_size,
                        overlap,
                    )
                )

                good_splits.clear()

            if rest:

                final_chunks.extend(
                    recursive_split(
                        split,
                        rest,
                        chunk_size,
                        overlap,
                    )
                )

            else:

                final_chunks.append(split)

    if good_splits:

        final_chunks.extend(
            merge_chunks(
                good_splits,
                sep,
                chunk_size,
                overlap,
            )
        )

    return final_chunks


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[str]:

    raw = recursive_split(
        text,
        SEPARATORS,
        chunk_size,
        overlap,
    )

    return [
        t.strip()
        for t in raw
        if len(t.strip()) > 20
    ]