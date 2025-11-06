using System;
using C0BR4ChessEngine.Core;
using C0BR4ChessEngine.Testing;

namespace C0BR4ChessEngine.BitboardTest
{
    class BitboardTestProgram
    {
        static void TestMain(string[] args)
        {
            Console.WriteLine("=== C0BR4 v2.2 Bitboard Implementation Test ===");
            Console.WriteLine("Testing the new bitboard system to resolve rule infractions...");
            
            try
            {
                BitboardValidationTest.RunBasicTests();
                BitboardValidationTest.TestProblematicPosition();
                
                Console.WriteLine("\n🎉 SUCCESS: Bitboard implementation is working!");
                Console.WriteLine("The rule infraction issues from v2.0 should now be resolved.");
                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ ERROR: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
            }
        }
    }
}
