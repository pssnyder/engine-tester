namespace C0BR4ChessEngine.Core
{
    public static class BoardHelper
    {
        public static int FileIndex(int squareIndex) => squareIndex % 8;
        public static int RankIndex(int squareIndex) => squareIndex / 8;
        public static int IndexFromCoord(int file, int rank) => rank * 8 + file;

        public static string SquareNameFromIndex(int index)
        {
            int file = FileIndex(index);
            int rank = RankIndex(index);
            return $"{(char)('a' + file)}{rank + 1}";
        }

        public static int SquareIndexFromName(string name)
        {
            if (name.Length != 2) return -1;
            int file = name[0] - 'a';
            int rank = name[1] - '1';
            if (file < 0 || file > 7 || rank < 0 || rank > 7) return -1;
            return IndexFromCoord(file, rank);
        }
    }
}
