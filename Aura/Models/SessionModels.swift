//
//  SessionModels.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import Foundation
import SwiftUI

// MARK: - Session State
enum SessionState {
    case home
    case scanning
    case intake
    case generating
    case reveal
    case tutorial
    case finished
}

// MARK: - Occasion
enum Occasion: String, CaseIterable, Identifiable {
    case dateNight = "Date Night"
    case office = "Office"
    case party = "Party"
    case custom = "Custom"
    
    var id: String { rawValue }
    
    var icon: String {
        switch self {
        case .dateNight: return "heart.fill"
        case .office: return "briefcase.fill"
        case .party: return "gift.fill"
        case .custom: return "pencil"
        }
    }
}

// MARK: - Glam Goal
enum GlamGoal: String, CaseIterable, Identifiable {
    case glowySkin = "Glowy Skin"
    case boldEye = "Bold Eye"
    case definedLips = "Defined Lips"
    
    var id: String { rawValue }
    
    var icon: String {
        switch self {
        case .glowySkin: return "sparkles"
        case .boldEye: return "eye.fill"
        case .definedLips: return "lips.fill"
        }
    }
}

// MARK: - Glam Level
class GlamLevel: ObservableObject {
    @Published var value: Double // 0.0 (Natural) to 1.0 (Full Beat)
    
    init(value: Double = 0.5) {
        self.value = value
    }
    
    var description: String {
        if value < 0.33 {
            return "Natural"
        } else if value < 0.67 {
            return "Soft Glam"
        } else {
            return "Full Beat"
        }
    }
}

// MARK: - Outfit Color
struct OutfitColor: Identifiable {
    let id = UUID()
    var color: Color
    var name: String?
}

// MARK: - Makeup Step
struct MakeupStep: Identifiable {
    let id = UUID()
    let stepNumber: Int
    let totalSteps: Int
    let title: String
    let instruction: String
    let product: String?
    let arGuidelines: ARGuidelines?
}

// MARK: - AR Guidelines
struct ARGuidelines {
    var cheekContour: Bool
    var foreheadContour: Bool
    var eyeGuidelines: Bool
    var lipGuidelines: Bool
}

// MARK: - Session
class Session: ObservableObject {
    @Published var state: SessionState = .home
    @Published var faceImage: UIImage?
    @Published var occasion: Occasion?
    @Published var customOccasion: String?
    @Published var glamLevel: GlamLevel = GlamLevel(value: 0.5)
    @Published var goals: Set<GlamGoal> = []
    @Published var outfitColors: [OutfitColor] = []
    @Published var generatedLookImage: UIImage?
    @Published var generatedLookDescription: String?
    @Published var tutorialSteps: [MakeupStep] = []
    @Published var currentStepIndex: Int = 0
    
    func reset() {
        state = .home
        faceImage = nil
        occasion = nil
        customOccasion = nil
        glamLevel = GlamLevel(value: 0.5)
        goals.removeAll()
        outfitColors.removeAll()
        generatedLookImage = nil
        generatedLookDescription = nil
        tutorialSteps.removeAll()
        currentStepIndex = 0
    }
}

