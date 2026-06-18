import java.io.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.Scanner;

/**
 * The Standard Camel: Dung & Trader Tycoon (Java Edition)
 * A zero-dependency, single-file Java terminal clicker game.
 * Features: Real-time idle dung generation (calculated on action delta-time),
 * fluctuating market prices, camel stable tiers, and gorgeous merchant upgrades!
 */
public class StandardCamel {
    private static final String SAVE_FILE = "standard_camel_save.txt";

    // Base Costs & Configs
    private static final Map<String, Integer> IDLE_RATES = new HashMap<>();
    static {
        IDLE_RATES.put("std", 1);
        IDLE_RATES.put("bac", 6);
        IDLE_RATES.put("rac", 35);
        IDLE_RATES.put("gld", 180);
    }

    private double coins = 100.0;
    private double dung = 0.0;
    private int stdCamels = 0;
    private int bacCamels = 0;
    private int racCamels = 0;
    private int gldCamels = 0;

    private int sauceUpg = 0;
    private int beardUpg = 0;
    private int maskUpg = 0;

    private int totalClicks = 0;
    private long lastTick = System.currentTimeMillis();
    private int marketPrice = 3;

    private int inflationStd = 50;
    private int inflationBac = 250;
    private int inflationRac = 1000;
    private int inflationGld = 5000;

    private final Random random = new Random();

    public static void main(String[] args) {
        StandardCamel game = new StandardCamel();
        game.load();
        game.runGameLoop();
    }

    public void runGameLoop() {
        Scanner scanner = new Scanner(System.in);
        String msg = "Welcome to Pollnivneach!";

        while (true) {
            clearScreen();
            double[] idleResult = processIdle();
            int rate = (int) idleResult[0];

            printHeader();
            System.out.println("=============================================================");
            System.out.printf(" 🪙  Coins (Dinars): $%d  |  💩  Ugthanki Dung: %d\n", (int) coins, (int) dung);
            System.out.printf(" Stable Output: %d Dung/sec   |  📈  Market Price: %d Dinars/Dung\n", rate, marketPrice);
            System.out.println("=============================================================");
            if (!msg.isEmpty()) {
                System.out.println(" 💬 Msg: " + msg);
                System.out.println("-------------------------------------------------------------");
                msg = "";
            }

            System.out.println(" [Enter] ➔ Click the Camel! (Harvest Dung)");
            System.out.println(" 1. 💰 Sell All Dung");
            System.out.println(" 2. 🐫 Buy Camels (Increase Idle Dung)");
            System.out.println(" 3. 🧪 Merchant Upgrades (Boost Click or Trade Values)");
            System.out.println(" 4. 📋 Check Stable Status");
            System.out.println(" 5. 🔄 Reset Game");
            System.out.println(" Q. ✕ Save & Quit");
            System.out.println("=============================================================");
            System.out.print(" Choose an action: ");

            String choice = scanner.nextLine().trim().toLowerCase();

            if (choice.isEmpty()) {
                int mult = click();
                msg = "Splop! You click the camel. (+" + mult + " Dung)";
                save();
            } else if (choice.equals("1")) {
                if (dung > 0) {
                    double bonus = beardUpg == 1 ? 1.15 : 1.0;
                    int payout = (int) (dung * marketPrice * bonus);
                    coins += payout;
                    dung = 0;
                    msg = String.format("Dinars claimed! Sold all dung for $%d Coins!", payout);
                    save();
                } else {
                    msg = "Stable dung is currently empty! Keep clicking!";
                }
            } else if (choice.equals("2")) {
                // Buy Camels submenu
                System.out.println("\n--- The Camel Stable ---");
                System.out.printf("1. Standard Camel [+1 Dung/s] - $%d Coins (Owned: %d)\n", inflationStd, stdCamels);
                System.out.printf("2. Bactrian Dromedary [+6 Dung/s] - $%d Coins (Owned: %d)\n", inflationBac, bacCamels);
                System.out.printf("3. Al Kharid Racer [+35 Dung/s] - $%d Coins (Owned: %d)\n", inflationRac, racCamels);
                System.out.printf("4. Golden Camel [+180 Dung/s] - $%d Coins (Owned: %d)\n", inflationGld, gldCamels);
                System.out.println("Press Enter to return.");
                System.out.print("\nBuy Camel (1-4): ");
                String sub = scanner.nextLine().trim();

                if (sub.equals("1")) {
                    if (coins >= inflationStd) {
                        coins -= inflationStd;
                        stdCamels++;
                        inflationStd = (int) (inflationStd * 1.15);
                        msg = "Purchased 1 Standard Camel safely!";
                        save();
                    } else {
                        msg = "Not enough Dinars!";
                    }
                } else if (sub.equals("2")) {
                    if (coins >= inflationBac) {
                        coins -= inflationBac;
                        bacCamels++;
                        inflationBac = (int) (inflationBac * 1.15);
                        msg = "Purchased 1 Bactrian Camel safely!";
                        save();
                    } else {
                        msg = "Not enough Dinars!";
                    }
                } else if (sub.equals("3")) {
                    if (coins >= inflationRac) {
                        coins -= inflationRac;
                        racCamels++;
                        inflationRac = (int) (inflationRac * 1.15);
                        msg = "Purchased 1 Al Kharid Racer safely!";
                        save();
                    } else {
                        msg = "Not enough Dinars!";
                    }
                } else if (sub.equals("4")) {
                    if (coins >= inflationGld) {
                        coins -= inflationGld;
                        gldCamels++;
                        inflationGld = (int) (inflationGld * 1.15);
                        msg = "Purchased 1 Golden Camel safely!";
                        save();
                    } else {
                        msg = "Not enough Dinars!";
                    }
                }
            } else if (choice.equals("3")) {
                // Buy Upgrades submenu
                System.out.println("\n--- Merchant Upgrades ---");
                if (sauceUpg == 0) {
                    System.out.println("1. Red Hot Kebab Sauce [Boosts clicks to +3 Dung] - $30 Coins");
                } else if (sauceUpg == 1) {
                    System.out.println("1. Extra-Hot Kebab Sauce [Boosts clicks to +8 Dung] - $120 Coins");
                } else if (sauceUpg == 2) {
                    System.out.println("1. Ali's Forbidden Elixir [Boosts clicks to +20 Dung] - $500 Coins");
                } else {
                    System.out.println("1. Kebab Sauce Mastery [MAX UNLOCKED]");
                }

                if (beardUpg == 0) {
                    System.out.println("2. Fake Beard & Disguise [Ali Morrisane trades +15% more Coins] - $150 Coins");
                } else {
                    System.out.println("2. Fake Beard & Disguise [UNLOCKED - Gorgeous Ali Mode Active]");
                }

                if (maskUpg == 0) {
                    System.out.println("3. Camel Mask [All idle dung increased by 25%] - $800 Coins");
                } else {
                    System.out.println("3. Camel Mask [UNLOCKED]");
                }
                System.out.println("Press Enter to return.");
                System.out.print("\nBuy Upgrade (1-3): ");
                String sub = scanner.nextLine().trim();

                if (sub.equals("1")) {
                    if (sauceUpg < 3) {
                        int cost = sauceUpg == 0 ? 30 : sauceUpg == 1 ? 120 : 500;
                        if (coins >= cost) {
                            coins -= cost;
                            sauceUpg++;
                            msg = "Kebab sauce upgraded successfully!";
                            save();
                        } else {
                            msg = "Insufficient Dinars!";
                        }
                    } else {
                        msg = "Already at Maximum Kebab Sauce level!";
                    }
                } else if (sub.equals("2")) {
                    if (beardUpg == 0) {
                        if (coins >= 150) {
                            coins -= 150;
                            beardUpg = 1;
                            msg = "Gorgeous Ali Disguise activated!";
                            save();
                        } else {
                            msg = "Insufficient Dinars!";
                        }
                    } else {
                        msg = "Already unlocked!";
                    }
                } else if (sub.equals("3")) {
                    if (maskUpg == 0) {
                        if (coins >= 800) {
                            coins -= 800;
                            maskUpg = 1;
                            msg = "Worship-grade Camel Mask equipped!";
                            save();
                        } else {
                            msg = "Insufficient Dinars!";
                        }
                    } else {
                        msg = "Already unlocked!";
                    }
                }
            } else if (choice.equals("4")) {
                System.out.println("\n--- Detailed Stable Status ---");
                System.out.printf(" Standard Camels: %d owned\n", stdCamels);
                System.out.printf(" Bactrian Camels: %d owned\n", bacCamels);
                System.out.printf(" Al Kharid Racers: %d owned\n", racCamels);
                System.out.printf(" Golden Camels: %d owned\n", gldCamels);
                System.out.println("---------------------------------------------");
                int clickMult = sauceUpg == 0 ? 1 : sauceUpg == 1 ? 3 : sauceUpg == 2 ? 8 : 20;
                System.out.printf(" Click Multiplier: +%d Dung per click\n", clickMult);
                System.out.printf(" Total Clicks: %d times\n", totalClicks);
                System.out.printf(" Gorgeous Disguise: %s\n", beardUpg == 1 ? "Active (+15% trade bonus)" : "Inactive");
                System.out.printf(" Camel Mask: %s\n", maskUpg == 1 ? "Active (+25% idle output)" : "Inactive");
                System.out.println("\nPress Enter to return.");
                scanner.nextLine();
            } else if (choice.equals("5")) {
                System.out.print("Confirm Game Reset? (y/n): ");
                if (scanner.nextLine().trim().toLowerCase().equals("y")) {
                    File file = new File(SAVE_FILE);
                    if (file.exists()) file.delete();
                    coins = 100.0;
                    dung = 0.0;
                    stdCamels = 0;
                    bacCamels = 0;
                    racCamels = 0;
                    gldCamels = 0;
                    sauceUpg = 0;
                    beardUpg = 0;
                    maskUpg = 0;
                    totalClicks = 0;
                    inflationStd = 50;
                    inflationBac = 250;
                    inflationRac = 1000;
                    inflationGld = 5000;
                    msg = "Stable reset. Starting fresh!";
                }
            } else if (choice.equals("q")) {
                save();
                System.out.println("\nStable Saved. Thanks for trading! Goodbye.\n");
                break;
            }
        }
    }

    private double[] processIdle() {
        long now = System.currentTimeMillis();
        double elapsedSeconds = (now - lastTick) / 1000.0;
        lastTick = now;

        if (random.nextDouble() < 0.25) {
            marketPrice = random.nextInt(4) + 2; // 2, 3, 4, 5
        }

        int rate = (stdCamels * IDLE_RATES.get("std")) +
                   (bacCamels * IDLE_RATES.get("bac")) +
                   (racCamels * IDLE_RATES.get("rac")) +
                   (gldCamels * IDLE_RATES.get("gld"));
        
        if (maskUpg == 1) {
            rate = (int) (rate * 1.25);
        }

        double generated = rate * elapsedSeconds;
        dung += generated;

        return new double[]{rate, generated};
    }

    private int click() {
        int mult = sauceUpg == 0 ? 1 :
                   sauceUpg == 1 ? 3 :
                   sauceUpg == 2 ? 8 : 20;
        dung += mult;
        totalClicks++;
        return mult;
    }

    private void printHeader() {
        System.out.println("        ,,__");
        System.out.println("       / o  `\\      ~ GORGEOUS ALI'S DISCOUNT CAMEL STORE ~");
        System.out.println("      |  __   \\");
        System.out.println("      | /  \\   |    \"Dung is the currency of the desert, friend!");
        System.out.println("      |/    \\  |     Keep clicking or let your stable grind!\"");
        System.out.println("             \\ \\");
        System.out.println("             / /__");
        System.out.println("            / /_ /");
        System.out.println("           /____/");
    }

    private void clearScreen() {
        try {
            if (System.getProperty("os.name").contains("Windows")) {
                new ProcessBuilder("cmd", "/c", "cls").inheritIO().start().waitFor();
            } else {
                System.out.print("\033[H\033[2J");
                System.out.flush();
            }
        } catch (Exception e) {
            // Fallback clear
            for (int i = 0; i < 50; i++) System.out.println();
        }
    }

    private void save() {
        try (PrintWriter writer = new PrintWriter(new FileWriter(SAVE_FILE))) {
            writer.println("coins=" + coins);
            writer.println("dung=" + dung);
            writer.println("stdCamels=" + stdCamels);
            writer.println("bacCamels=" + bacCamels);
            writer.println("racCamels=" + racCamels);
            writer.println("gldCamels=" + gldCamels);
            writer.println("sauceUpg=" + sauceUpg);
            writer.println("beardUpg=" + beardUpg);
            writer.println("maskUpg=" + maskUpg);
            writer.println("totalClicks=" + totalClicks);
            writer.println("inflationStd=" + inflationStd);
            writer.println("inflationBac=" + inflationBac);
            writer.println("inflationRac=" + inflationRac);
            writer.println("inflationGld=" + inflationGld);
        } catch (IOException e) {
            System.err.println("Could not save: " + e.getMessage());
        }
    }

    private void load() {
        File file = new File(SAVE_FILE);
        if (!file.exists()) return;

        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split("=");
                if (parts.length < 2) continue;
                String key = parts[0].trim();
                String val = parts[1].trim();

                switch (key) {
                    case "coins": coins = Double.parseDouble(val); break;
                    case "dung": dung = Double.parseDouble(val); break;
                    case "stdCamels": stdCamels = Integer.parseInt(val); break;
                    case "bacCamels": bacCamels = Integer.parseInt(val); break;
                    case "racCamels": racCamels = Integer.parseInt(val); break;
                    case "gldCamels": gldCamels = Integer.parseInt(val); break;
                    case "sauceUpg": sauceUpg = Integer.parseInt(val); break;
                    case "beardUpg": beardUpg = Integer.parseInt(val); break;
                    case "maskUpg": maskUpg = Integer.parseInt(val); break;
                    case "totalClicks": totalClicks = Integer.parseInt(val); break;
                    case "inflationStd": inflationStd = Integer.parseInt(val); break;
                    case "inflationBac": inflationBac = Integer.parseInt(val); break;
                    case "inflationRac": inflationRac = Integer.parseInt(val); break;
                    case "inflationGld": inflationGld = Integer.parseInt(val); break;
                }
            }
        } catch (IOException | NumberFormatException e) {
            System.err.println("Could not load save: " + e.getMessage());
        }
        lastTick = System.currentTimeMillis();
    }
}
