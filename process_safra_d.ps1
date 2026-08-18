$ErrorActionPreference = "Stop"

$houses = @(
    "549 - محمد سلمان أحمد إبراهيم العويناتي",
    "550 - خالد صالح عبد الله النوبي",
    "550A - مظهر حسين فضل حسين كرم علي غلام",
    "551A - محمد عثمان حاجي فقير محمد",
    "552 - سحر ميرزا افتخار أنور بيك",
    "572 - خليل أحمد الحمد العساف",
    "576 - يحيى مساعد محسن الشرفي",
    "610 - طلال محسن ناصر أحمد",
    "612 - قصي علي العون",
    "614 - عبد الباقي حسن داد محمد البلوشي",
    "615 - أمينة محمد عبد الله محمد المطوع",
    "624 - أحمد مراد محمد مراد",
    "679 - جميل عبد الله محمد عبدي البلوشي",
    "681 - إيمان مبارك حسن محمد أحمد الرويعي",
    "685 - صالح قاسم حسين عسكر",
    "687 - خليف مشبهر سالم",
    "697 - عادل عبد الواحد البلوشي",
    "713 - مبارك علي محمد علي",
    "715 - خالد محمد أشرف دين محمد نواب دين",
    "723 - محمد علي ميرزا"
)

foreach ($house in $houses) {
    Write-Host "Processing House: $house"
    
    $path = "D:\areas\Safra D\$house"
    
    Write-Host "Running create for $house..."
    python src/main.py create "$path" --model gemma-4-31b-it --categorization-model gemini-3.5-flash-lite
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Create command failed for '$house' with exit code $LASTEXITCODE. Halting script."
        exit $LASTEXITCODE
    }
    
    Write-Host "Running verify for $house..."
    python src/main.py verify "$path"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Verify command failed for '$house' with exit code $LASTEXITCODE. Halting script."
        exit $LASTEXITCODE
    }
}

Write-Host "Successfully processed all 20 houses."
