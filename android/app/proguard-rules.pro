# xpass — R8 rules
-keep class com.google.zxing.** { *; }
-dontwarn com.google.zxing.**

# เก็บชื่อคลาสที่ใช้ผ่าน reflection น้อยที่สุด
-keepattributes *Annotation*
