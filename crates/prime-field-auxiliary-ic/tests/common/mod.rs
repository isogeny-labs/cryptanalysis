// Public correctness fixtures; source is the frozen standalone experiment.
mod multi_tile;
pub use multi_tile::{MAPS31_MULTI, ROOTS31_MULTI, TERMINAL31_MULTI};
use prime_field_auxiliary_ic::{AuxiliaryMap, Relation, SignedRelation};
pub const ROOTS31: [u64; 32] = [
    3, 308768278, 1213058799, 1950178058, 1620095117, 1685732321, 845665662, 1760557235,
    1393679185, 536276641, 1896314920, 1171458932, 1533993268, 1528659296, 1851652048, 987367763,
    1431655765, 1908835095, 1857409341, 975624154, 80168778, 1101836261, 985108144, 2084456163,
    753804470, 1900319349, 1900239952, 141165527, 98625645, 1491270739, 2008905047, 1560638367,
];
pub const MAPS31: [AuxiliaryMap; 5] = [
    AuxiliaryMap {
        r: 0,
        offset: 0,
        residue: 1,
    },
    AuxiliaryMap {
        r: 2,
        offset: 6,
        residue: 8,
    },
    AuxiliaryMap {
        r: 262150,
        offset: 786438,
        residue: 3145792,
    },
    AuxiliaryMap {
        r: 135006214,
        offset: 403445766,
        residue: 562160130,
    },
    AuxiliaryMap {
        r: 199756251,
        offset: 1939860868,
        residue: 1327400300,
    },
];
pub const TERMINAL31: u64 = 1569594640;
pub const RELATIONS31: [Relation; 13] = [
    Relation {
        a: 1914864060,
        b: 227513669,
        decomposition: SignedRelation {
            i: 0,
            j: 8,
            negative_i: false,
            negative_j: true,
        },
    },
    Relation {
        a: 1867242651,
        b: 1465106331,
        decomposition: SignedRelation {
            i: 9,
            j: 11,
            negative_i: true,
            negative_j: true,
        },
    },
    Relation {
        a: 595423595,
        b: 594250840,
        decomposition: SignedRelation {
            i: 2,
            j: 4,
            negative_i: false,
            negative_j: false,
        },
    },
    Relation {
        a: 1432539520,
        b: 1501318730,
        decomposition: SignedRelation {
            i: 8,
            j: 14,
            negative_i: true,
            negative_j: false,
        },
    },
    Relation {
        a: 554692589,
        b: 683168887,
        decomposition: SignedRelation {
            i: 1,
            j: 16,
            negative_i: true,
            negative_j: false,
        },
    },
    Relation {
        a: 1265639284,
        b: 1772566897,
        decomposition: SignedRelation {
            i: 4,
            j: 7,
            negative_i: true,
            negative_j: true,
        },
    },
    Relation {
        a: 1498614098,
        b: 1044397679,
        decomposition: SignedRelation {
            i: 0,
            j: 9,
            negative_i: false,
            negative_j: true,
        },
    },
    Relation {
        a: 414865127,
        b: 1260338174,
        decomposition: SignedRelation {
            i: 0,
            j: 3,
            negative_i: true,
            negative_j: false,
        },
    },
    Relation {
        a: 1016448,
        b: 1959209645,
        decomposition: SignedRelation {
            i: 4,
            j: 14,
            negative_i: false,
            negative_j: true,
        },
    },
    Relation {
        a: 1378890758,
        b: 2039419614,
        decomposition: SignedRelation {
            i: 1,
            j: 15,
            negative_i: true,
            negative_j: true,
        },
    },
    Relation {
        a: 433019161,
        b: 2006419393,
        decomposition: SignedRelation {
            i: 3,
            j: 6,
            negative_i: false,
            negative_j: true,
        },
    },
    Relation {
        a: 809409559,
        b: 736145210,
        decomposition: SignedRelation {
            i: 7,
            j: 7,
            negative_i: true,
            negative_j: true,
        },
    },
    Relation {
        a: 1040672564,
        b: 718769385,
        decomposition: SignedRelation {
            i: 9,
            j: 14,
            negative_i: true,
            negative_j: false,
        },
    },
];
pub const ROOTS61: [u64; 32] = [
    6,
    395890123215756913,
    610585164357590277,
    913497785930989002,
    1217414149585871507,
    1508099967281696778,
    1953253191104847773,
    2207048013161703894,
    198481170864541458,
    1508498306582554346,
    931159788809297444,
    1030488001761034205,
    2002908291332150179,
    444489011042517429,
    1575542111712463488,
    313029963040179116,
    1921535841011411626,
    240164655318685601,
    1487637275939242859,
    1973835114489893635,
    1932590054440442878,
    1452887792496524200,
    17070860110369423,
    188514938209984399,
    2291829279086248013,
    47549478630589224,
    1853225821800759213,
    1902335226722929220,
    881010439957904205,
    361104833483686751,
    913518387134928166,
    2083631704789468863,
];
pub const MAPS61: [AuxiliaryMap; 5] = [
    AuxiliaryMap {
        r: 0,
        offset: 0,
        residue: 1,
    },
    AuxiliaryMap {
        r: 2,
        offset: 6,
        residue: 8,
    },
    AuxiliaryMap {
        r: 8589934598,
        offset: 25769803782,
        residue: 103079215168,
    },
    AuxiliaryMap {
        r: 562975723749382,
        offset: 1688875631640582,
        residue: 33777821857874432,
    },
    AuxiliaryMap {
        r: 1896362194504047049,
        offset: 1074022813821472081,
        residue: 2206629613183517689,
    },
];
pub const TERMINAL61: u64 = 1359448921955946756;
