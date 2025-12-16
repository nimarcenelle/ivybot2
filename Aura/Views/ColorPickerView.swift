//
//  ColorPickerView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct ColorPickerView: View {
    @Binding var selectedColors: [OutfitColor]
    @Environment(\.dismiss) var dismiss
    @State private var currentHue: Double = 0.5
    @State private var currentSaturation: Double = 1.0
    @State private var currentBrightness: Double = 1.0
    
    var body: some View {
        NavigationView {
            ZStack {
                LinearGradient(
                    colors: [Color.black.opacity(0.9), Color.purple.opacity(0.3)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 24) {
                    Text("Select up to 3 colors")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.white)
                        .padding(.top, 20)
                    
                    // Color wheel
                    GeometryReader { geometry in
                        let size = min(geometry.size.width, geometry.size.height) - 40
                        
                        ZStack {
                            // Color wheel
                            ForEach(0..<360, id: \.self) { angle in
                                let hue = Double(angle) / 360.0
                                let color = Color(hue: hue, saturation: 1.0, brightness: 1.0)
                                
                                Path { path in
                                    let center = CGPoint(x: size/2, y: size/2)
                                    let radius = size / 2
                                    let startAngle = Angle(degrees: Double(angle))
                                    let endAngle = Angle(degrees: Double(angle + 1))
                                    
                                    path.move(to: center)
                                    path.addArc(
                                        center: center,
                                        radius: radius,
                                        startAngle: startAngle,
                                        endAngle: endAngle,
                                        clockwise: false
                                    )
                                    path.closeSubpath()
                                }
                                .fill(color)
                            }
                            
                            // Inner circle (white to black gradient)
                            Circle()
                                .fill(
                                    RadialGradient(
                                        colors: [
                                            Color.white,
                                            Color(hue: currentHue, saturation: currentSaturation, brightness: currentBrightness)
                                        ],
                                        center: .center,
                                        startRadius: 0,
                                        endRadius: size / 3
                                    )
                                )
                                .frame(width: size / 1.5, height: size / 1.5)
                            
                            // Selection indicator
                            Circle()
                                .stroke(Color.white, lineWidth: 3)
                                .frame(width: 30, height: 30)
                                .offset(
                                    x: cos(currentHue * 2 * .pi) * (size / 2 - 15),
                                    y: sin(currentHue * 2 * .pi) * (size / 2 - 15)
                                )
                        }
                        .frame(width: size, height: size)
                        .gesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { value in
                                    let center = CGPoint(x: size/2, y: size/2)
                                    let deltaX = value.location.x - center.x
                                    let deltaY = value.location.y - center.y
                                    let distance = sqrt(deltaX * deltaX + deltaY * deltaY)
                                    
                                    if distance > size / 3 {
                                        // Outer ring - adjust hue
                                        let angle = atan2(deltaY, deltaX)
                                        currentHue = (angle + .pi) / (2 * .pi)
                                    } else {
                                        // Inner circle - adjust saturation and brightness
                                        currentSaturation = min(1.0, distance / (size / 3))
                                        currentBrightness = 1.0 - (distance / (size / 3)) * 0.5
                                    }
                                }
                        )
                    }
                    .frame(height: 300)
                    .padding()
                    
                    // Selected colors display
                    if !selectedColors.isEmpty {
                        HStack(spacing: 16) {
                            ForEach(selectedColors) { outfitColor in
                                ZStack(alignment: .topTrailing) {
                                    Circle()
                                        .fill(outfitColor.color)
                                        .frame(width: 60, height: 60)
                                        .overlay(
                                            Circle()
                                                .stroke(Color.white.opacity(0.3), lineWidth: 2)
                                        )
                                    
                                    Button(action: {
                                        selectedColors.removeAll { $0.id == outfitColor.id }
                                    }) {
                                        Image(systemName: "xmark.circle.fill")
                                            .font(.system(size: 20))
                                            .foregroundColor(.white)
                                            .background(Circle().fill(Color.black.opacity(0.5)))
                                    }
                                    .offset(x: 5, y: -5)
                                }
                            }
                        }
                        .padding()
                    }
                    
                    // Current color preview
                    VStack(spacing: 12) {
                        Circle()
                            .fill(Color(hue: currentHue, saturation: currentSaturation, brightness: currentBrightness))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Circle()
                                    .stroke(Color.white.opacity(0.3), lineWidth: 2)
                            )
                        
                        Button(action: {
                            if selectedColors.count < 3 {
                                let newColor = OutfitColor(
                                    color: Color(hue: currentHue, saturation: currentSaturation, brightness: currentBrightness)
                                )
                                selectedColors.append(newColor)
                            }
                        }) {
                            Text(selectedColors.count < 3 ? "Add Color" : "Maximum 3 colors")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                                .background(
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(.ultraThinMaterial)
                                        
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(
                                                LinearGradient(
                                                    colors: [Color.white.opacity(0.2), Color.white.opacity(0.05)],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                )
                                            )
                                    }
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                )
                        }
                        .disabled(selectedColors.count >= 3)
                        .opacity(selectedColors.count >= 3 ? 0.5 : 1.0)
                    }
                    .padding(.horizontal, 20)
                    
                    Spacer()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                    .foregroundColor(.white)
                }
            }
        }
    }
}

#Preview {
    ColorPickerView(selectedColors: .constant([]))
}

