using System;
public class Program
{
    public static void Main()
    {
        string a = Console.ReadLine();
        string b = Console.ReadLine();
        bool isAdmin = Program.Login(a, b);
        if (isAdmin)
        {
            Console.WriteLine("Ugurlu");
        }
        else
        {
            Console.WriteLine("ugursuz");
        }
    }
    static bool Login(string name, string password)
    {
        if (name == "qurban" && password == "1234")
        {
            return true;
        }
        return false;
    }
}
